"""The night, walked for him (phase 7): Spellbound, and the guide of the first night.

Her letter is soaked in her venom, and since he first touched it his thoughts have kept turning to the oak. Let it lead
him, and it does: in through the roots, careful on her silk, up to her guests, down to supper when she calls, up to
the crown, and to the light - taking what's there to take, looking closer at what's there to see, choosing his words
for him. Plain Python: the tests let it walk a whole night.

    nav = Nav(tree, web)                    where he is; a way from there to there, through the oak
        nav.where(night)  -> ("tunnel", along) | ("silk", piece) | ("ledge", s) | ("floor", None)
        nav.route(night, goal) -> [(x, y, z)] points to walk through
        goals: ("floor", x, z) ("ledge", s, x, z) ("tunnel", along, across) ("loom", x, z) ("crown", x, z)
    director = Director(night, guide=False)
        director.step(dt, night, inp) -> [requests for the view]: ("dawn",)   - drives inp itself
        director.hold(seconds)        stand still a while (something to read)
        director.idle                 nothing left to do this act
    choose_line(choices, kinds_of, moods)  the line he'd say (her moods' scoring of what each would mean)
    best_gift(night)                  what to offer her now, if anything's worth it
"""
import math

from . import tree as T
from .web import H_LOOM

WALK_TURN = 2.6                 # (radians a second he turns, walking)
NEAR = 0.42                     # (close enough to a point on the way)
STUCK = 3.5                     # (seconds without getting closer: he's set on his way again)


def _yaw_to(x0, z0, x1, z1):
    return math.atan2(x1 - x0, -(z1 - z0))


def _wrap(a):
    return (a + math.pi) % math.tau - math.pi


class Nav:
    def __init__(self, tree, web):
        self.tree, self.web = tree, web
        k = T.PITCH / math.tau
        self.s_loom = H_LOOM / k                                       # (where the ledge meets her loom)
        start, run = next((s, r) for n, s, r in T.LANDINGS if n == "crown")
        self.s_crown = start + run * 0.5

    # ---- points on the way --------------------------------------------------------------------------------------
    def ledge_pt(self, s, inset=0.5):
        t = self.tree
        th = t.theta_of(s)
        h = t.ledge_h(s)
        r = t.base_r(th, h + 0.5) - T.LEDGE_W * inset
        return (math.cos(th) * r, h, math.sin(th) * r)

    def landing_s(self, name, along=0.5):
        start, run = next((s, r) for n, s, r in T.LANDINGS if n == name)
        return start + run * along

    def s_at(self, x, z, y):
        """The turn of the ledge nearest this height, at this angle."""
        th = math.atan2(z, x)
        best = None
        for s in self.tree.ledge_turns(th):
            h = self.tree.ledge_h(s)
            if h is not None and (best is None or abs(h - y) < best[0]):
                best = (abs(h - y), s)
        return best[1] if best else 0.3

    # ---- where he is --------------------------------------------------------------------------------------------
    def where(self, night):
        t = self.tree
        tun = t.in_tunnel(night.x, night.z)
        if tun and tun[0] > 0.2:
            return ("tunnel", tun[0])
        if night.on is not None:
            return ("silk", night.on)
        th = math.atan2(night.z, night.x)
        d = math.hypot(night.x, night.z)
        for s in t.ledge_turns(th):
            h = t.ledge_h(s)
            if h is not None and h > 0.3 and abs(h - night.y) < 0.35 and d >= t.base_r(th, h + 0.5) - T.LEDGE_W - 0.1:
                return ("ledge", s)
        return ("floor", None)

    # ---- a way through ------------------------------------------------------------------------------------------
    def _along(self, s0, s1):
        out = []
        n = max(1, int(abs(s1 - s0) / 0.22))
        for i in range(1, n + 1):
            out.append(self.ledge_pt(s0 + (s1 - s0) * i / n))
        return out

    def _to_floor(self, here, night):
        """From wherever he is, down onto the hollow's floor: -> points."""
        kind, v = here
        if kind == "tunnel":
            pts, a = [], v
            while a > 0.6:
                a = max(0.6, a - 1.5)
                x, z = self._tun(a)
                pts.append((x, 0.0, z))
            return pts + [self._floor_pt(*self.tree.tunnel_point(-1.2, 0.0))]
        if kind == "silk":
            s = self.s_loom if v is self.web.loom else self.s_crown if v is self.web.crown else None
            if s is None:                                           # (a strand: back to the nearer end)
                u, _a = v.locate(night.x, night.z)
                end = v.a if u < 0.5 else v.b
                s = self.s_at(end[0], end[2], end[1])
            return [self.ledge_pt(s, 0.5)] + self._along(s, 0.15) + [self._floor_pt(*self._foot_in())]
        if kind == "ledge":
            return self._along(v, 0.15) + [self._floor_pt(*self._foot_in())]
        return []

    def _tun(self, along):
        return self.tree.tunnel_point(along, 0.0)

    def _floor_pt(self, x, z):
        return (x, self.tree.ground(x, z), z)

    def _foot_in(self):
        """A little in from the ledge's foot, on the floor."""
        x, _y, z = self.ledge_pt(0.15, 0.5)
        k = 1.0 - 1.4 / max(1.0, math.hypot(x, z))
        return (x * k, z * k)

    def route(self, night, goal):
        here = self.where(night)
        kind = goal[0]
        # the same place already: straight there
        if kind == "tunnel" and here[0] == "tunnel":
            return [(*self.tree.tunnel_point(goal[1], goal[2]), 0.0)]
        if kind == "floor" and here[0] == "floor":
            return [self._floor_pt(goal[1], goal[2])]
        if kind in ("loom", "crown") and here[0] == "silk" and here[1] is (self.web.loom if kind == "loom" else
                                                                           self.web.crown):
            return [(goal[1], 0.0, goal[2])]
        if kind == "ledge" and here[0] == "ledge":
            return self._along(here[1], goal[1]) + ([(goal[2], 0.0, goal[3])] if goal[2] is not None else [])
        if kind in ("ledge", "loom", "crown") and here[0] == "silk" and here[1] in (self.web.loom, self.web.crown):
            s0 = self.s_loom if here[1] is self.web.loom else self.s_crown
            pts = [self.ledge_pt(s0, 0.5)]
            return pts + self._from_ledge(s0, goal)
        # otherwise: down to the floor (if he's not there), and from the floor to where it is
        pts = [] if here[0] == "floor" else self._to_floor(here, night)
        if kind == "tunnel":
            mouth = self.tree.tunnel_point(-0.8, 0.0)
            return pts + [self._floor_pt(*mouth)] + [(*self.tree.tunnel_point(a, 0.0), 0.0)
                                                     for a in (0.6, max(0.6, goal[1]))] + \
                [(*self.tree.tunnel_point(goal[1], goal[2]), 0.0)]
        if kind == "floor":
            return pts + [self._floor_pt(goal[1], goal[2])]
        foot = self.ledge_pt(0.15, 0.5)
        return pts + [self._floor_pt(*self._foot_in()), foot] + self._from_ledge(0.15, goal)

    def _from_ledge(self, s0, goal):
        kind = goal[0]
        if kind == "ledge":
            return self._along(s0, goal[1]) + ([(goal[2], 0.0, goal[3])] if goal[2] is not None else [])
        s1 = self.s_loom if kind == "loom" else self.s_crown
        x, _y, z = self.ledge_pt(s1, 0.5)
        disc = self.web.loom if kind == "loom" else self.web.crown
        th = math.atan2(z, x)
        r = disc.rim(th)
        return self._along(s0, s1) + [(math.cos(th) * (r - 0.6), 0.0, math.sin(th) * (r - 0.6)),
                                      (goal[1], 0.0, goal[2])]


# ---- his words -------------------------------------------------------------------------------------------------------
def score_kinds(kinds):
    from .moods import HEARD
    total = 0.0
    for k in kinds:
        f, pa, hu, su, rg = HEARD.get(k, (0, 0, 0, 0, 0))
        total += f + 1.5 * rg + 0.5 * pa - su - 0.2 * hu
    return total


def choose_line(choices):
    """choices: [(text, kinds, flag)] -> the index he'd choose: what she'd like best - never a lie, never to stay."""
    best, at = None, 0
    for i, (_text, kinds, flag) in enumerate(choices):
        sc = score_kinds(kinds) - (100 if flag in ("stay",) or "lie" in kinds or "lewd" in kinds else 0)
        if best is None or sc > best:
            best, at = sc, i
    return at


def best_gift(night, tiers=("delight",)):
    from .offerings import KEPT, worth
    best = None
    for item in night.pack:
        if item in KEPT:
            continue
        tier = worth(item, night)[0]
        if tier in tiers and best is None:
            best = item
    return best


# ---- the director ----------------------------------------------------------------------------------------------------
class Director:
    def __init__(self, night, guide=False):
        self.nav = Nav(night.tree, night.web)
        self.guide = guide
        self.tasks = []
        self.act = None
        self.path = []
        self.goal = None
        self.t = 0.0
        self.hold_until = 0.0
        self.best_d, self.best_t = 1e9, 0.0
        self.replan_t = 0.0
        self.task_t = 0.0
        self.idle = False
        self.wander = 0
        self.shake_t = -9.0
        self.dawned = False

    def hold(self, seconds):
        self.hold_until = max(self.hold_until, self.t + seconds)

    # ---- what he means to do, act by act ------------------------------------------------------------------------
    def _plan(self, n):
        from .spells import mark_at
        act = n.acts.act
        T_ = []
        if act == "threshold":
            if "mark_roots" not in n.spells.marks_seen:
                T_.append({"do": "light", "at": ("tunnel", 6.5, 0.0), "look": mark_at(n.tree, "tunnel", 6.5)})
            if "ring" not in n.taken:
                T_.append({"do": "take", "item": "ring", "at": ("tunnel", 4.4, 0.0)})
            if "mouse" not in n.taken:
                T_.append({"do": "take", "item": "mouse", "at": ("tunnel", 0.75, -0.3)})
            T_.append({"do": "onto", "at": "loom"})
        elif act in ("gallery", "audience"):
            for spot in n.cocoons.spots[:4]:
                if spot["id"] not in n.cocoons.burst:
                    T_.append({"do": "cocoon", "id": spot["id"]})
            if "moths" not in n.taken:
                T_.append({"do": "take", "item": "moths", "at": self._before(n.finds.spots["moths"], 0.95, n)})
            for spot in n.cocoons.spots[4:6]:
                if spot["id"] not in n.cocoons.burst:
                    T_.append({"do": "cocoon", "id": spot["id"]})
            if "mark_tally" not in n.spells.marks_seen:
                s = self.nav.landing_s("gallery")
                x, _y, z = self.nav.ledge_pt(s, 0.2)
                T_.append({"do": "light", "at": ("ledge", s, x, z), "look": mark_at(n.tree, "gallery", 0.0)})
            T_.append({"do": "wander"})
        elif act == "supper":
            s = self.nav.landing_s("larder")
            x, _y, z = self.nav.ledge_pt(s, -0.4)
            T_.append({"do": "go", "at": ("ledge", s, x, z)})
            T_.append({"do": "wander"})
        elif act == "crown":
            if "crown" in n.acts.outcomes:
                T_.append({"do": "dawn"})
            else:
                if "mark_crown" not in n.spells.marks_seen:
                    s = self.nav.s_crown
                    x, _y, z = self.nav.ledge_pt(s, 0.1)
                    T_.append({"do": "light", "at": ("ledge", s, x, z), "look": mark_at(n.tree, "crown", 0.0)})
                if not self.guide and "unnamed" not in n.cocoons.burst:
                    T_.append({"do": "cocoon", "id": "unnamed"})
                T_.append({"do": "onto", "at": "crown"})
        self.tasks = T_

    def _before(self, p, dist, n):
        """A place to stand, `dist` in from p toward the hollow's middle (on the floor, or the ledge it's on)."""
        x, y, z = p
        r = math.hypot(x, z)
        k = max(0.0, 1.0 - dist / max(r, 1e-6))
        sx, sz = x * k, z * k
        if y < 1.2 and n.tree.in_tunnel(sx, sz) is None:
            return ("floor", sx, sz)
        return ("ledge", self.nav.s_at(sx, sz, y - 0.5), sx, sz)

    def _cocoon_goal(self, n, sid):
        spot = next(s for s in n.cocoons.spots if s["id"] == sid)
        x, y, z = spot["pos"]
        if spot["floor"] < 0.5:
            return self._before(spot["pos"], 1.3, n), spot
        r = math.hypot(x, z)
        k = 1.0 - 1.15 / r
        s = self.nav.s_at(x * k, z * k, spot["floor"])
        return ("ledge", s, x * k, z * k), spot

    # ---- a step -------------------------------------------------------------------------------------------------
    def step(self, dt, n, inp):
        self.t += dt
        out = []
        inp.forward = inp.strafe = 0.0
        inp.hurry = inp.jump = False
        if n.dying is not None or n.ending is not None:
            return out
        if n.lamp.state == "out" and self.t - self.shake_t > 1.6:         # (his lantern, shaken back to life)
            self.shake_t = self.t
            n.lamp.shake()
        if n.venom.active and "antidote" in n.pack and not self.guide:      # (her venom out of him)
            n.drink()
        if n.quiet:                                                         # (her scene: he's hers to talk to)
            return out
        if self.t < self.hold_until or n.venom.vision is not None:
            return out
        if self.guide:                                                      # (the first night: only where it's sent)
            if not self.tasks:
                return out
        elif n.acts.act != self.act:
            self.act = n.acts.act
            self._plan(n)
            self.path, self.goal = [], None
        if not self.guide and n.venom.active and n.venom.revealed and "antidote" not in n.taken and \
                not any(t["do"] == "take" and t.get("item") == "antidote" for t in self.tasks):
            self.tasks.insert(0, {"do": "take", "item": "antidote",
                                  "at": self._before(n.finds.spots["antidote"], 0.9, n)})
        if not self.tasks and not self.guide:
            self._plan(n)
        if not self.tasks:
            return out
        task = self.tasks[0]
        self.idle = task["do"] in ("wander", "dawn")
        done = self._do(task, n, inp, dt, out)
        if done:
            self.tasks.pop(0)
            self.path, self.goal = [], None
            self.task_t = 0.0
            if self.guide:
                out.append(("done", task["do"]))
        return out

    def _do(self, task, n, inp, dt, out):
        kind = task["do"]
        if kind == "dawn":
            if not self.dawned:
                self.dawned = True
                out.append(("dawn",))
            return False
        if kind == "wander":                                                # (nothing asked of him: he looks about)
            if self.goal is None or not self.path:
                self.wander += 1
                a = self.wander * 2.399
                rr = 2.0 + 1.5 * math.sin(self.wander * 1.7)
                if n.acts.act == "supper":
                    return True                                             # (on: to her larder)
                self.goal = ("floor", math.cos(a) * rr, math.sin(a) * rr)
                self.path = self.nav.route(n, self.goal)
                self.hold(2.5)
            self._walk(n, inp, dt)
            return False
        if kind == "onto":
            goal = (task["at"], 0.0, 0.0) if task["at"] == "loom" else (task["at"], 0.4, 0.3)
            if n.on is (n.web.loom if task["at"] == "loom" else n.web.crown):
                return True
            if self._go(n, inp, dt, goal):
                self.goal = None                                            # (there, but not on it: again)
            return False
        if kind == "go":
            if self._go(n, inp, dt, task["at"]):
                return "look" not in task or self._face(n, inp, dt, task["look"])
            return False
        if kind == "light":
            if self._go(n, inp, dt, task["at"]):
                if self._face(n, inp, dt, task["look"]):
                    n.spells.rest["light"] = min(n.spells.rest["light"], n.spells.t)
                    n.cast("light")
                    self.hold(2.0)
                    return True
            return False
        if kind == "take":
            item = task["item"]
            if item in n.pack or (item in n.taken and item not in n.finds.dropped):
                return True
            goal = task["at"]
            if self._go(n, inp, dt, goal):
                if self._face(n, inp, dt, n.finds.where(item, n)):
                    if len(n.pack) >= 4:
                        self._make_room(n, item)
                    n.examine()
                    self.task_t += dt
                    if item in n.pack or self.task_t > 2.0:
                        return True
            return False
        if kind == "cocoon":
            goal, spot = self._cocoon_goal(n, task["id"])
            if self._go(n, inp, dt, goal):
                if self._face(n, inp, dt, spot["pos"]):
                    if spot["id"] not in n.cocoons.burst:
                        n.examine()
                        self.hold(2.5)
                        return False
                    keep = n.KEEPSAKES.get(spot["id"])
                    if keep and keep not in n.taken:
                        if len(n.pack) >= 4:
                            self._make_room(n, keep)
                        n.examine()
                        self.task_t += dt
                        return keep in n.taken or self.task_t > 2.0
                    return True
            return False
        return True

    def _make_room(self, n, wanted):
        """A full satchel: the least of what's in it, set down."""
        from .offerings import worth
        rank = {"delight": 0, "plain": 1, "insult": 2}
        cand = [i for i in n.pack if i != "antidote"]
        if not cand:
            return
        worst = max(cand, key=lambda i: rank[worth(i, n)[0]])
        n.held = worst
        n.put_down()

    # ---- going, and looking -------------------------------------------------------------------------------------
    def _go(self, n, inp, dt, goal):
        """Toward goal; -> True once he's there."""
        if goal != self.goal:
            self.goal = goal
            self.path = self.nav.route(n, goal)
            self.best_d, self.best_t = 1e9, self.t
            self.replan_t = self.t
        if not self.path:
            return True
        self._walk(n, inp, dt)
        return not self.path

    def _walk(self, n, inp, dt):
        if not self.path:
            return
        px, _py, pz = self.path[0]
        d = math.hypot(px - n.x, pz - n.z)
        last = len(self.path) == 1
        if d < (0.28 if last else NEAR):
            self.path.pop(0)
            self.best_d, self.best_t = 1e9, self.t
            return
        if d < self.best_d - 0.05:
            self.best_d, self.best_t = d, self.t
        elif self.t - self.best_t > STUCK:                                  # (caught on something: on, past it)
            y = n.floor_at(px, pz, n.y + 1.0)
            n.x, n.z, n.y, n.vy = px, pz, y, 0.0
            self.path.pop(0)
            self.best_d, self.best_t = 1e9, self.t
            return
        want = _yaw_to(n.x, n.z, px, pz)
        err = _wrap(want - inp.yaw)
        inp.yaw += max(-WALK_TURN * dt, min(WALK_TURN * dt, err))
        inp.pitch += (-0.12 - inp.pitch) * min(1.0, dt * 2.0)                # (eyes on the way ahead)
        inp.forward = 1.0 if abs(err) < 0.5 else 0.25 if abs(err) < 1.2 else 0.0
        if last and d < 0.8:
            inp.forward *= 0.5

    def _face(self, n, inp, dt, p):
        """Turn to look at p: -> True once he's looking at it."""
        ex, ey, ez = n.eye
        want_y = _yaw_to(ex, ez, p[0], p[2])
        want_p = math.atan2(p[1] - ey, math.hypot(p[0] - ex, p[2] - ez))
        ey_ = _wrap(want_y - inp.yaw)
        inp.yaw += max(-3.0 * dt, min(3.0 * dt, ey_))
        inp.pitch += max(-2.0 * dt, min(2.0 * dt, want_p - inp.pitch))
        return abs(ey_) < 0.08 and abs(want_p - inp.pitch) < 0.08
