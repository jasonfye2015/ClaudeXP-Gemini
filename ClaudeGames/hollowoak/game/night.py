"""The night: Claude inside the Hollow Oak, from dusk on - where he stands, where he looks, his lantern, the clock, and
(for now) the only signs of her: eyes, high in the dark, watching him climb; her small ones; and her silk, which
carries every step he takes on it to her.

On a strand he sways: the faster he goes, the more; A and D lean against it. Lean too far and he slips off. What she
feels through the silk is kept in `silk` - gentle steps, hurried ones, slips, falls into her web - for her to judge.

    night = Night()
    night.step(dt, inp)            (inp: an Input - forward, strafe, yaw, pitch, hurry)
    night.eye                      where he looks from
    night.events                   what happened, for the view: ("place", name, line), ...

Plain Python: the view draws it, the tests walk it."""
import math
import random

from . import tree as T
from .den import Den
from .babies import Danglers, Swarm
from .brood import Brood
from .condition import Condition
from .crawlers import Crawlers
from .death import Death
from .lantern import Lantern
from .moods import Moods
from .acts import Acts
from .cocoons import Cocoons
from .ending import Ending
from .mother import Mother
from .sky import Sky
from .web import BRIDGE_HALF, Bridge, Web

EYE = 0.52                     # (a little smaller than the Timeline's other first-person games: she is very large)
RADIUS = 0.21
HEIGHT = 0.64                  # (room he needs over his head)
WALK = 1.35                    # (unhurried: she feels every step)
HURRY = 3.45                   # (a run: Shift)
JUMP = 3.9                     # (Space: about half his height)
GRAVITY = 16.0
# his balance on a strand: a lean that springs back, pushed about by the strand's bounce - the more, the faster he goes
SWAY_SPRING = 2.4
SWAY_DAMP = 1.5
SWAY_LEAN = 2.6                # (how hard A or D leans him back)
SWAY_TEETER = 0.65
STEP_SILK = 0.55               # (a step, on silk: the creak she hears, the tremor she feels)

PLACES = {
    "tunnel": ("The roots", "A way in through the roots of the Hollow Oak. Dry leaves, and something that isn't wind."),
    "hollow": ("The Hollow", "The inside of the tree, going up and up into the dark. A ledge winds up the wall."),
    "gallery": ("The gallery", "A chamber in the wood. The walls here are hung with something wrapped in silk."),
    "larder": ("The larder", "A low chamber that smells of old honey and older meat."),
    "high hollow": ("The high hollow", "Wind moves through the wood here. You are very far from the ground."),
    "crown": ("The crown", "The top of the oak, broken open to the sky. The moon is very close."),
}


class Input:
    def __init__(self):
        self.forward = 0.0
        self.strafe = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.hurry = False
        self.jump = False              # (Space: set by the view, used once)


class Night:
    def __init__(self, seed=None):
        self.tree = T.Tree()
        self.den = Den(self.tree)
        self.web = Web(self.tree)
        self.rng = random.Random(seed)
        sx, sz, facing = self.tree.start
        self.x, self.z = sx, sz
        self.y = self.tree.floor_at(sx, sz, 1.0)
        self.yaw = math.atan2(math.cos(facing), -math.sin(facing))
        self.pitch = 0.0
        self.vy = 0.0
        self.time = 0.0
        self.sky = Sky(random.Random(self.rng.random()))                 # (the clock and the weather: game/sky.py)
        self.lantern = True                  # (he carries it: whether it gives any light is the lamp's affair)
        self.lamp = Lantern(self.rng)
        self.events = []
        self.seen = set()
        self.place = None
        self.moved = 0.0
        self.her = Mother(self.tree, random.Random(self.rng.random()))     # (Ysmeine: on the wall, in the dark)
        self.cocoons = Cocoons(self.tree)                                   # (her guests, wrapped)
        self.moods = Moods()                                                # (how she regards him: hidden)
        # the small ones' eyes, low in the dark: six at a time, each in one of the den's dark places
        spots = list(range(len(self.den.lurks)))
        self.rng.shuffle(spots)
        self.lurkers = [{"spot": k, "alpha": 0.0, "hidden_until": self.rng.uniform(0, 6), "blink_at": self.rng.uniform(1, 6),
                         "eyes": self.rng.choice((2, 2, 4, 6)), "seed": self.rng.random()} for k in spots[:6]]
        # the silk: what he stands on (None, or a piece of her web), his balance, and what she has felt
        self.on = None
        self.sway, self.sway_v, self.push = 0.0, 0.0, 0.0
        self.teetering = False
        self.tremor = 0.0                    # (how hard the silk is shaking now: it dies away)
        self.silk = {"gentle": 0.0, "hurried": 0.0, "slips": 0, "falls": 0, "touched": False}
        self._silk_step = 0.0
        self._fall_from = self.y
        self.inp_hurry = False
        self.moved_now = 0.0
        self.brood = Brood(self.tree, self.web, random.Random(self.rng.random()))
        self.crawlers = Crawlers(random.Random(self.rng.random()))     # (the small ones that cross his eyes)
        self.danglers = Danglers(random.Random(self.rng.random()))     # (and drop before his face)
        self.swarm = Swarm(random.Random(self.rng.random()))           # (and come for the lantern, in the dark)
        self.body = Condition(random.Random(self.rng.random()))        # (how he's holding up: the orbs)
        self.dying = None                                              # (a Death, once something gives out)
        self.ending = None                                             # (an Ending, when dawn comes)
        self.acts = Acts()                                             # (the night's shape: game/acts.py)
        self.flags = {}                                                # (what he's chosen tonight: to stay...)
        self.lies = 0
        self.quiet = False                                             # (in her scenes: nothing small onto him)
        self.met = {}                                                  # (her scenes so far: name -> how it ended)
        self.eye_h = EYE
        self.roll = 0.0

    # ---- where he is --------------------------------------------------------------------------------------------
    @property
    def eye(self):
        return (self.x, self.y + self.eye_h, self.z)

    def floor_at(self, x, z, feet):
        """The highest thing he can stand on under (x, z): the tree, or her silk."""
        f = self.tree.floor_at(x, z, feet)
        w = self.web.floor_at(x, z, feet)
        return w[0] if w is not None and w[0] > f else f

    def _support(self):
        """The piece of silk he stands on, if it's silk that holds him up."""
        w = self.web.floor_at(self.x, self.z, self.y)
        if w is None or abs(w[0] - self.y) > 0.02 or w[0] < self.tree.floor_at(self.x, self.z, self.y) + 0.02:
            return None
        return w[1]

    def manner(self):
        """How he has gone on her silk, as she'd read it: -1 (prey: scrambling, falling) to 1 (careful, unhurried)."""
        s = self.silk
        good = s["gentle"]
        bad = s["hurried"] * 2.0 + s["slips"] * 4.0 + s["falls"] * 6.0
        return 0.0 if good + bad < 1e-6 else (good - bad) / (good + bad)

    def where(self):
        t = self.tree
        if t.in_tunnel(self.x, self.z) and t.in_tunnel(self.x, self.z)[0] > 0.2:
            return "tunnel"
        return t.landing_at(self.x, self.z, self.y) or "hollow"

    def lantern_reach(self):
        """How far his lantern's light reaches, and how bright it is: a short, dim throw in the close dark of the
        root tunnel, opening out as he comes into the hollow - and all of it as the lamp allows (flickering,
        sputtering, out). -> (reach, strength)"""
        lvl = self.lamp.level
        tun = self.tree.in_tunnel(self.x, self.z)
        k = max(0.0, min(1.0, (tun[0] - 0.2) / 2.5)) if tun else 0.0     # (0 in the hollow, 1 a few steps into the roots)
        reach = (6.0 - 4.2 * k) * (0.35 + 0.65 * min(1.0, lvl))
        return reach, (1.0 - 0.72 * k) * lvl

    @property
    def clock(self):
        return self.sky.clock

    def clock_words(self):
        return self.sky.hour_words()

    # ---- a step ------------------------------------------------------------------------------------------------
    def step(self, dt, inp):
        dt = min(dt, 0.05)
        self.time += dt
        if self.dying is not None:                                     # (it's over: what happens to him now)
            self.sky.step(dt)
            self.events.extend(self.dying.step(dt, self))
            self.body.dying_heart(dt, self.dying.t)
            return
        if self.ending is not None:                                    # (dawn: how it ends)
            self.sky.step(dt)
            self.events.extend(self.ending.step(dt))
            return
        first = len(self.events)                                       # (what happens this step, from here)
        self.events.extend(self.sky.step(dt))
        for e in self.acts.step(dt, self):
            self.events.append(e)
            if e == ("act", "dawn"):                                   # (the light: how it ends, decided by all of it)
                self.ending = Ending(self.acts.decide(self))
                return
        turn = (inp.yaw - self.yaw) / dt if dt > 0 else 0.0
        self.yaw, self.pitch = inp.yaw, max(-1.45, min(1.45, inp.pitch))
        before = self.moved
        self._move(dt, inp)
        self.moved_now = self.moved - before
        self._balance(dt, inp, turn)
        self.tremor *= math.exp(-dt / 1.3)
        p = self.where()
        if p != self.place:
            self.place = p
            if p not in self.seen:
                self.seen.add(p)
                name, line = PLACES[p]
                self.events.append(("place", name, line))
        lamp_events = self.lamp.step(dt)
        for e in lamp_events:
            self.events.append(("lantern", e))
        self.events.extend(self.moods.step(dt, self, self.events[first:]))
        for e in self.her.step(dt, self):
            self.events.append(e)
            if e == ("her", "bite") and self.bitten():
                return
        self._lurk(dt)
        self.events.extend(self.brood.step(dt, self.eye, self.inp_hurry, self.lantern_reach()[0] if self.lantern else 0.0))
        if not self.quiet:
            self.events.extend(self.crawlers.step(dt))
            self.events.extend(self.danglers.step(dt, self))
            self.events.extend(self.swarm.step(dt, self.lamp.state, lamp_events))
        self.events.extend(self.body.step(dt, self, self.events[first:]))
        gone = self.body.spent()
        if gone is not None:
            self.collapse(gone)

    def examine(self):
        """F: a closer look at the wrapped thing before him. If it's whole, it splits - and they pour out of it."""
        spot = self.cocoons.near(self)
        if spot is None:
            return None
        for e in self.cocoons.examine(self, spot):
            self.events.append(e)
            if e[3]:                                            # (the burst)
                self.brood.pour_out(spot["pos"], spot["floor"], 34)
                for _ in range(2):
                    self.crawlers.scurry(0.08)                  # (and some onto his face)
                self.body.sanity = max(0.0, self.body.sanity - 4.0)
                self.body.startle += 30.0
                self.moods.suspicion = min(100.0, self.moods.suspicion + (8.0 if spot["id"] == "unnamed" else 2.0))
                self.moods.fascination = min(100.0, self.moods.fascination + 1.0)
                self.tremor += 2.5                              # (she felt her guest disturbed)
        return spot

    def bitten(self):
        """Her bite: venom, and her hunger eased a while. A second is Supper. -> True if that was the end of him."""
        self.moods.bit()
        self.body.poison = min(100.0, self.body.poison + 30.0)
        self.body.health = max(0.0, self.body.health - 8.0)
        self.body.startle += 40.0
        self.tremor += 3.0
        if self.moods.bites >= 2:
            self.collapse("bite")
            return True
        return False

    def collapse(self, cause):
        """Something gave out: down he goes, and they come."""
        self.dying = Death(self, cause, random.Random(self.rng.random()))
        self.crawlers.runs.clear()
        self.crawlers.swipe_at = None
        self.danglers.hanging.clear()
        self.swarm.babies.clear()
        self.on, self.sway = None, 0.0
        self.events.append(("collapse", cause))

    # ---- on her silk -------------------------------------------------------------------------------------------
    def _balance(self, dt, inp, turn):
        """His lean on a strand: pushed by the strand's bounce (more the faster he goes, and when he turns sharply),
        sprung back by his own sense of balance, and leant against with A and D. Too far, and he's off."""
        if not isinstance(self.on, Bridge):
            self.sway *= math.exp(-dt * 4)
            self.sway_v = 0.0
            self.teetering = False
            return
        moving = abs(inp.forward) > 0.01
        agit = 0.35 + (0.7 if moving else 0.0) + (3.2 if moving and inp.hurry else 0.0) + min(1.5, abs(turn) * 0.35)
        agit += min(1.0, self.tremor * 0.15)
        self.push += (self.rng.gauss(0.0, 1.0) * 5.0 - self.push * 2.5) * dt          # (the bounce: wandering)
        force = self.push * agit - SWAY_SPRING * self.sway - SWAY_DAMP * self.sway_v + inp.strafe * SWAY_LEAN
        self.sway_v += force * dt
        self.sway += self.sway_v * dt
        if abs(self.sway) > SWAY_TEETER and not self.teetering:
            self.teetering = True
            self.events.append(("silk", "teeter"))
        elif abs(self.sway) < SWAY_TEETER * 0.6:
            self.teetering = False
        if abs(self.sway) >= 1.0:                                     # (he's off: over the side of the strand)
            b = self.on
            u, _across = b.locate(self.x, self.z)
            off = (1.0 if self.sway > 0 else -1.0) * (BRIDGE_HALF + RADIUS + 0.05)
            self.x = b.a[0] + b.dir[0] * b.length * u + b.side[0] * off
            self.z = b.a[2] + b.dir[1] * b.length * u + b.side[1] * off
            self.silk["slips"] += 1
            self.tremor += 4.0
            self.events.append(("silk", "slip"))
            self.sway, self.sway_v, self.on = 0.0, 0.0, None

    def _on_silk(self, dist, hurry):
        """A step's worth of him on her silk: the tremor, and what she makes of it."""
        self.tremor += dist * (1.6 if hurry else 0.45)
        self.silk["hurried" if hurry else "gentle"] += dist
        self._silk_step += dist
        if self._silk_step >= STEP_SILK:
            self._silk_step -= STEP_SILK
            self.events.append(("silk", "step", hurry))

    def _lurk(self, dt):
        """The small eyes near the ground: they show in the dark, a way off; they blink; and when he comes near - or
        his lantern finds them - they're gone, and turn up again somewhere else in a while."""
        ex, ey, ez = self.eye
        reach, _k = self.lantern_reach() if self.lantern else (0.0, 0.0)
        taken = {l["spot"] for l in self.lurkers}
        for l in self.lurkers:
            x, y, z = self.den.lurks[l["spot"]]
            d = math.dist((x, y, z), (ex, ey, ez))
            if self.time < l["hidden_until"]:
                l["alpha"] = max(0.0, l["alpha"] - dt * 4)
                continue
            if d < max(2.6, reach * 0.6) or d > 15:
                l["alpha"] = max(0.0, l["alpha"] - dt * (6 if d < 6 else 1))
                if l["alpha"] == 0.0 and d < 6:                       # (scattered: somewhere else, later)
                    free = [k for k in range(len(self.den.lurks)) if k not in taken and
                            math.dist(self.den.lurks[k], (ex, ey, ez)) > 6]
                    if free:
                        taken.discard(l["spot"])
                        l["spot"] = self.rng.choice(free)
                        taken.add(l["spot"])
                    l["hidden_until"] = self.time + self.rng.uniform(4, 11)
                    self.events.append(("scatter", (x, y, z)))
                continue
            l["alpha"] = min(1.0, l["alpha"] + dt * 0.5)
            if self.time > l["blink_at"] + 0.16:
                l["blink_at"] = self.time + self.rng.uniform(1.5, 7.0)

    def lurking(self):
        """The small eyes showing now: [(position, alpha, how many eyes, seed)] - shut for a moment as they blink."""
        out = []
        for l in self.lurkers:
            if l["alpha"] <= 0.01:
                continue
            shut = l["blink_at"] <= self.time <= l["blink_at"] + 0.16
            out.append((self.den.lurks[l["spot"]], l["alpha"] * (0.08 if shut else 1.0), l["eyes"], l["seed"]))
        return out

    def _move(self, dt, inp):
        t = self.tree
        self.inp_hurry = inp.hurry
        fwd, side = inp.forward, inp.strafe
        bridge = self.on if isinstance(self.on, Bridge) else None
        if bridge is not None:
            side = 0.0                                         # (on a strand, A and D are for balance)
        n = math.hypot(fwd, side)
        if n > 1:
            fwd, side = fwd / n, side / n
        speed = HURRY if inp.hurry else WALK
        sy, cy = math.sin(self.yaw), math.cos(self.yaw)
        dx = (sy * fwd + cy * side) * speed * dt
        dz = (-cy * fwd + sy * side) * speed * dt
        if bridge is not None:                                 # (along it, and only along it: he keeps to it)
            along = dx * bridge.dir[0] + dz * bridge.dir[1]
            _u, across = bridge.locate(self.x, self.z)
            pull = -across * min(1.0, dt * 3.0)                # (his feet find the middle of it)
            dx = bridge.dir[0] * along + bridge.side[0] * pull
            dz = bridge.dir[1] * along + bridge.side[1] * pull
        on_ground = self.y <= self.floor_at(self.x, self.z, self.y) + 0.01
        if inp.jump:                                            # (a jump: off the ground, or off her silk)
            inp.jump = False
            if on_ground and self.vy == 0.0:
                self.vy = JUMP
                self._fall_from = self.y
                self.events.append(("jump",))
                if self.on is not None:                         # (she feels that: a scramble, not a step)
                    self.tremor += 1.2
                    self.silk["hurried"] += 0.6
                    if isinstance(self.on, Bridge):
                        self.sway_v += self.rng.gauss(0.0, 1.4)
                self.on = None
                self.y += 0.02
                on_ground = False
        for mx, mz in ((dx, dz), (dx, 0.0), (0.0, dz)):        # (straight on, or sliding along what's in the way)
            if not (mx or mz):
                continue
            nx, nz = self.x + mx, self.z + mz
            f = self.floor_at(nx, nz, self.y)
            if f > self.y + T.STEP:
                continue
            if t.can_stand(nx, nz, max(self.y, f) if on_ground else self.y, RADIUS, HEIGHT):
                self.x, self.z = nx, nz
                d = math.hypot(mx, mz)
                self.moved += d
                if self.on is not None and on_ground:
                    self._on_silk(d, inp.hurry)
                break
        f = self.floor_at(self.x, self.z, self.y)
        if self.y > f + 0.01:                                 # (falling: off the ledge's edge, or a strand - or jumping)
            if self.vy == 0.0:
                self._fall_from = self.y
            self.on = None
            self.vy -= GRAVITY * dt
            self.y = max(f, self.y + self.vy * dt)
            ceil = t.ceiling_at(self.x, self.z, f)
            if ceil is not None and self.vy > 0 and self.y + HEIGHT > ceil:     # (his head on the roof)
                self.y, self.vy = ceil - HEIGHT, 0.0
            self._fall_from = max(self._fall_from, self.y)
            if self.y == f:
                if self.vy < -9:
                    self.events.append(("fall", -self.vy))
                self.vy = 0.0
                self.on = self._support()
                if self.on is not None and self._fall_from - self.y > 0.8:     # (caught in her web: she felt that)
                    self.silk["falls"] += 1
                    self.tremor += 3.0 + (self._fall_from - self.y) * 0.4
                    self.events.append(("silk", "caught", self.on.name))
        else:
            self.y, self.vy = f, 0.0
            was = self.on
            self.on = self._support()
            if self.on is not None and was is None and not self.silk["touched"]:
                self.silk["touched"] = True
                self.events.append(("silk", "first", self.on.name))

    # ---- her ---------------------------------------------------------------------------------------------------
    @property
    def eye_alpha(self):
        return self.her.alpha

    def eyes(self):
        """Her eyes, if they show: [{"pos", "alpha"}] (they blink, now and then)."""
        pos, alpha = self.her.eyes()
        if alpha <= 0.01:
            return []
        blink = 0.15 if (self.time * 0.37) % 4.0 < 0.12 else 1.0
        return [{"pos": pos, "alpha": alpha * blink}]
