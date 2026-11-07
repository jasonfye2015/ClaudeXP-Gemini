"""Auto-play: Claude plays himself. On a floor of the Deep he fights what he sees, takes everything lying about,
opens every chest (and the doors he has keys for, and the levers, and the brazier trial, and the cracked walls), hunts
down every monster left, explores every square, and then takes the stairs home. In Thornwick he sees to his things -
wears the best gear he has, builds the best wands he can from every body and part, learns what Mother Wren teaches,
tends the farm, cooks and eats, sells what's left and buys potions - and goes down again to where the run has got to.
After the hundredth floor it goes on: endless.

    bot = Autopilot()
    bot.drive(game, inp, dt)      every frame, before game.step: it sets inp (and calls the game's own actions)

It uses nothing a player couldn't: the floor's squares, what's in sight, the map he's walked."""
import heapq
import math
import random

from . import data as D
from . import food as F
from . import items as I
from . import shop, skills
from .levels import STEP

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
SEE = 5                                   # (squares about him counted as seen as he goes)
FLOOR_TIME = 480.0                        # (seconds on a floor before he heads for the stairs whatever's left)
GIVE_UP = 720.0                           # (and before he goes home however he can)
SKILL_ORDER = ["kindling", "thick_skin", "deep_well", "flowing_mind", "warded_robes", "quick_hands", "keen_eye",
               "second_wind", "fire_lore", "rime_lore", "storm_lore", "venom_lore", "arcane_weight", "fleet_foot",
               "hearty", "thrift", "bloodthirst", "attunement", "gold_sense", "mastery", "bulwark", "archmage"]
WEIGHTS = {"life": 0.5, "mana": 0.35, "armour": 0.9, "regen": 5.0, "power": 3.0, "haste": 2.5, "swift": 1.2,
           "fire": 0.7, "frost": 0.7, "storm": 0.7, "venom": 0.7, "arcane": 0.7, "leech": 4.0, "find": 0.4,
           "crit": 2.0, "life%": 2.0, "mana%": 1.5}


class Autopilot:
    def __init__(self):
        self.level = None
        self.say = []                     # (what it's doing, for the HUD: the newest last)

    # ---- every frame ---------------------------------------------------------------------------------------------
    def drive(self, g, inp, dt):
        if g.level is not self.level:
            self._new_level(g)
        if g.depth == 0:
            self._town(g, inp, dt)
            return
        self.t += dt
        inp.forward = inp.strafe = 0.0
        inp.fire = inp.jump = False
        inp.run = True
        self._mark_seen(g)
        self._potions(g)
        foe = self._foe(g)
        if foe is not None:
            self._fight(g, inp, foe, dt)
            return
        if self._puzzles_at_hand(g, inp):
            return
        if self.t > GIVE_UP:
            self._note(g, "Auto-play: this floor's had long enough - home.")
            g.stairs_home()
            return
        self.replan -= dt
        if self.goal is None or self.replan <= 0 or not self.path:
            self.replan = 0.6
            self._choose(g)
        self._follow(g, inp, dt)

    def _new_level(self, g):
        L = self.level = g.level
        self.t = 0.0
        self.seen = set()
        self.goal, self.path, self.replan = None, [], 0.0
        self.blocked = {}                 # (goals given up on: key -> until when)
        self.hand = {}                    # (things being shot at where he stands: key -> since when)
        self.last_pos, self.still = (g.x, g.z), 0.0
        self.town_t, self.town_done = 0.0, False
        self.fit, self.fit_ver = {}, None
        if L.depth:
            self.trap_cells = {(t["x"], t["y"]) for t in getattr(L, "traps", ())}

    def _note(self, g, text):
        self.say = (self.say + [text])[-3:]
        g.events.append(("toast", text, (0.7, 0.9, 1.0)))

    # ---- seeing --------------------------------------------------------------------------------------------------
    def _mark_seen(self, g):
        cx, cy = int(g.x), int(g.z)
        L = g.level
        for y in range(cy - SEE, cy + SEE + 1):
            for x in range(cx - SEE, cx + SEE + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= SEE * SEE and 0 <= x < L.w and 0 <= y < L.h:
                    self.seen.add((x, y))

    def _visible(self, g, x, z, y):
        ex, ey, ez = g.eye
        return g.level.line_of_sight(x, z, y, ex, ez, ey)

    # ---- fighting ------------------------------------------------------------------------------------------------
    def _foe(self, g):
        best, bd = None, 1e9
        for m in g.monsters:
            if m.dead:
                continue
            d = math.hypot(m.x - g.x, m.z - g.z)
            if d > 15 or (not m.awake and d > 9):
                continue
            if not self._visible(g, m.x, m.z, m.centre_y):
                continue
            score = d - (6 if m.awake else 0) - (4 if m.guardian else 0)
            if score < bd:
                best, bd = m, score
        return best

    def _aim(self, g, inp, x, y, z):
        ex, ey, ez = g.eye
        inp.yaw = math.atan2(x - ex, -(z - ez))
        inp.pitch = math.atan2(y - ey, max(0.1, math.hypot(x - ex, z - ez)))

    def _fight(self, g, inp, m, dt):
        self._aim(g, inp, m.x, m.centre_y, m.z)
        inp.fire = True
        d = math.hypot(m.x - g.x, m.z - g.z)
        inp.run = False
        if m.kind != "ranged" and d < 2.6:                # (a biter close: back off as he shoots)
            inp.forward = -1.0
            inp.strafe = math.sin(self.t * 1.7)
        elif d > 9:
            inp.forward = 0.6
        else:
            inp.strafe = math.sin(self.t * 1.3) * 0.8      # (a little side to side: harder to hit)
        self._unstick(g, inp, dt)
        self.goal = None

    def _potions(self, g):
        p = g.player
        if p.life < p.max_life() * 0.4 and p.potions.get("health", 0) > 0:
            g.drink("health")
        s = p.wand_stats()
        if s and p.mana < s["mana"] * 1.5 and p.potions.get("mana", 0) > 0:
            g.drink("mana")
        if p.life < p.max_life() * 0.18 and p.potions.get("health", 0) == 0 and p.potions.get("return", 0) > 0:
            self._note(g, "Auto-play: too hurt - a Scroll of Return.")
            g.read_return()

    # ---- the puzzles' moments: things to do where he stands -------------------------------------------------------
    def _puzzles_at_hand(self, g, inp):
        L = g.level
        what, _label = g.near()
        if what:
            k = what[0]
            if k == "chest":
                g.open_chest(what[1])
                self.goal = None
                return True
            if k == "door":
                g.open_door(what[1])
                self.goal = None
                return True
            if k == "lever":
                g.pull_lever(what[1])
                self.goal = None
                return True
        # a brazier in sight and cold, the trial not done: light it
        if L.braziers and L.trial and not L.trial["done"]:
            for k, b in enumerate(L.braziers):
                if not b["lit"] and math.hypot(b["x"] - g.x, b["z"] - g.z) < 8 and self._at_hand(("brazier", k)) and                         self._visible(g, b["x"], b["z"], b["y"] + 0.5):
                    self._aim(g, inp, b["x"], b["y"] + 0.5, b["z"])
                    inp.fire = True
                    return True
        # a cracked wall straight ahead of the square he stands on: shoot it
        cx, cy = int(g.x), int(g.z)
        for (wx, wy), sw in getattr(L, "secret_walls", {}).items():
            if not sw["open"] and abs(wx - cx) + abs(wy - cy) == 1 and self._at_hand(("crack", wx, wy)):
                inp.forward = 0.0
                self._aim(g, inp, wx + 0.5, sw["f"] + 0.9, wy + 0.5)
                inp.fire = True
                return True
        return False

    def _at_hand(self, key):
        """Whether to keep at a thing he's shooting at: six seconds, then leave it a minute."""
        if self.blocked.get(key, -1) > self.t:
            return False
        start = self.hand.setdefault(key, self.t)
        if self.t - start > 6.0:
            self.blocked[key] = self.t + 60
            del self.hand[key]
            return False
        return True

    # ---- choosing where to go -------------------------------------------------------------------------------------
    def _dist_map(self, g):
        """The walk's cost to every square from where he is (traps dear, water slow, closed doors shut unless he has
        their key) -> {square: cost}, {square: previous}."""
        L = g.level
        shut = {(d["x"], d["y"]) for d in L.doors if not d["open"] and d["colour"] not in g.keys}
        start = (int(g.x), int(g.z))
        dist, prev = {start: 0.0}, {}
        q = [(0.0, start)]
        while q:
            c, (x, y) = heapq.heappop(q)
            if c > dist.get((x, y), 1e18):
                continue
            for dx, dy in DIRS:
                n = (x + dx, y + dy)
                if not L.open_at(*n) or n in shut or abs(L.floor[n[1], n[0]] - L.floor[y, x]) > STEP:
                    continue
                if (x, y) != start and not self._fits(L, (x, y), (dx, dy)):   # (out of where he stands: he's there)
                    continue
                step = 1.0 + (12.0 if n in self.trap_cells else 0.0) + (1.0 if n in L.water else 0.0)
                nc = c + step
                if nc < dist.get(n, 1e18):
                    dist[n], prev[n] = nc, (x, y)
                    heapq.heappush(q, (nc, n))
        return dist, prev

    def _fits(self, L, c, d):
        """Whether his body fits from square c to its neighbour that way - things in the way and all (as the
        floor's own walkable test looks: in small steps). Remembered until something on the floor breaks."""
        ver = (getattr(L, "version", 0), getattr(L, "mesh_version", 0))
        if self.fit_ver != ver:
            self.fit, self.fit_ver = {}, ver
        key = (c, d)
        ok = self.fit.get(key)
        if ok is None:
            x, y = c
            nx, ny = x + d[0], y + d[1]
            ok = abs(L.floor[ny, nx] - L.floor[y, x]) <= STEP
            if ok:
                foot = max(L.floor[y, x], L.floor[ny, nx]) - 0.01
                ok = all(L.can_stand(x + 0.5 + d[0] * t, y + 0.5 + d[1] * t, 0.26, foot, doors=False) for t in (0.25, 0.5, 0.75, 1.0))
            self.fit[key] = ok
        return ok

    def _choose(self, g):
        L = g.level
        dist, prev = self._dist_map(g)
        now = self.t
        cands = []                                         # (priority, cost, key, target square, approach)

        def add(pri, key, sq, near=False):
            if self.blocked.get(key, -1) > now:
                return
            if near:                                       # (stand beside it, not on it)
                opts = [(sq[0] + dx, sq[1] + dy) for dx, dy in DIRS if (sq[0] + dx, sq[1] + dy) in dist]
                if not opts:
                    return
                sq = min(opts, key=lambda s: dist[s])
            if sq in dist:
                cands.append((pri, dist[sq], key, sq))
        if now < FLOOR_TIME:
            for pk in L.pickups:
                add(0, ("pk", id(pk)), (int(pk["x"]), int(pk["z"])))
            for i, c in enumerate(L.chests):
                if not c["opened"] and not c.get("broken") and not c.get("stash"):
                    add(1, ("chest", i), (int(c["x"]), int(c["z"])), near=True)
            for i, d in enumerate(L.doors):
                if not d["open"] and d["colour"] in g.keys:
                    add(1, ("door", i), (d["x"], d["y"]), near=True)
            for i, lv in enumerate(L.levers):
                if not lv["pulled"]:
                    add(2, ("lever", i), (lv["x"], lv["y"]))
            if L.trial and not L.trial["done"] and any(not b["lit"] for b in L.braziers):
                add(2, ("trial",), (L.trial["x"], L.trial["y"]))
            for (wx, wy), sw in getattr(L, "secret_walls", {}).items():
                if not sw["open"] and (wx, wy) in self.seen:
                    add(2, ("crack", wx, wy), (wx, wy), near=True)
            for m in g.monsters:
                if not m.dead:
                    add(3, ("m", m.id), (int(m.x), int(m.z)))
            frontier = [sq for sq in dist if sq not in self.seen]
            if frontier:
                sq = min(frontier, key=lambda s: dist[s])
                add(4, ("explore", sq), sq)
        # with nothing else: the guardian, then the stairs (or into the Gauntlet's hall, to wake it)
        if L.stairs:
            sq = (int(L.stairs[0]), int(L.stairs[1]))
            add(5, ("stairs",), sq)
        if not cands:
            self.goal, self.path = None, []
            if self.t > FLOOR_TIME + 30:
                self._note(g, "Auto-play: no way to the stairs - home by the long way.")
                g.stairs_home()
            return
        cands.sort(key=lambda c: (c[0], c[1]))
        pri, cost, key, sq = cands[0]
        if pri == 5 and L.guardian and not g.guardian_down and not L.rush:
            alive = [m for m in g.monsters if not m.dead and m.guardian]
            if alive:
                key, sq = ("m", alive[0].id), (int(alive[0].x), int(alive[0].z))
        path = [sq]
        while path[-1] in prev:
            path.append(prev[path[-1]])
        path.reverse()
        if key != self.goal:
            self.goal_since = self.t
        self.goal, self.path, self.goal_sq = key, path[1:] or [sq], sq

    def _follow(self, g, inp, dt):
        L = g.level
        if not self.path:
            return
        tx, ty = self.path[0]
        cx, cy = tx + 0.5, ty + 0.5
        if math.hypot(cx - g.x, cy - g.z) < 0.35:
            self.path.pop(0)
            if not self.path:
                self._arrived(g)
                return
            tx, ty = self.path[0]
            cx, cy = tx + 0.5, ty + 0.5
        inp.yaw = math.atan2(cx - g.x, -(cy - g.z))
        inp.pitch = 0.0
        inp.forward = 1.0
        if self.t - getattr(self, "goal_since", 0) > 40:   # (forty seconds after one thing: leave it a while)
            self.blocked[self.goal] = self.t + 90
            self.goal, self.path = None, []
        self._unstick(g, inp, dt)
        del L

    def _arrived(self, g):
        key = self.goal
        self.goal = None
        if key == ("stairs",):
            L = g.level
            if L.guardian and not g.guardian_down:
                return                                     # (sealed: the Gauntlet wakes as he stands in its hall)
            self._note(g, f"Auto-play: floor {g.depth} done - home to see to things.")
            g.stairs_home()
        elif key:                                          # (there, and it's still there: leave it a while)
            self.blocked[key] = self.t + (8 if key[0] == "m" else 45)

    def _unstick(self, g, inp, dt):
        moved = math.hypot(g.x - self.last_pos[0], g.z - self.last_pos[1])
        self.last_pos = (g.x, g.z)
        if (inp.forward or inp.strafe) and moved < 0.4 * dt:
            self.still += dt
        else:
            self.still = max(0.0, self.still - dt * 2)
        if self.still > 0.8:
            inp.jump = True
            inp.strafe = 1.0 if int(self.t) % 2 else -1.0
            inp.fire = True                                # (most things in the way break)
            inp.pitch = -0.25
        if self.still > 3.0 and self.goal:
            self.blocked[self.goal] = self.t + 60
            self.goal, self.path, self.still = None, [], 0.0

    # ---- home -------------------------------------------------------------------------------------------------------
    def _town(self, g, inp, dt):
        inp.forward = inp.strafe = 0.0
        inp.fire = inp.jump = False
        self.town_t += dt
        if not self.town_done and self.town_t > 1.0:
            self.town_done = True
            for line in housekeeping(g, random.Random(g.player.stats["kills"])):
                self._note(g, "Auto-play: " + line)
        if self.town_done and self.town_t > 6.0:
            n = g.run_floor
            self._note(g, f"Auto-play: down to floor {n}.")
            g.go_floor(n)


# ---- seeing to his things ------------------------------------------------------------------------------------------
def gear_score(it, element="arcane"):
    if not it:
        return 0.0
    w = dict(WEIGHTS)
    w[element] = 2.5
    return sum(w.get(k, 0.3) * v for k, v in it["stats"].items())


def best_wand(bodies, parts):
    """The strongest wand that can be built from these bodies and parts (each part used once):
    -> (body, [parts]) or None. Greedy: the part that adds most, slot by slot."""
    best = None
    for w in bodies:
        trial = dict(w, parts=[None] * len(w["parts"]))
        pool = list(parts)
        for k in range(len(trial["parts"])):
            base = I.wand_stats(trial)["dps"]
            pick, gain = None, 0.0
            for p in pool:
                trial["parts"][k] = p
                s = I.wand_stats(trial)
                v = s["dps"] * (1 + 0.15 * s["homing"] / 3 + 0.1 * s["pierce"] + 0.05 * s["bounce"])
                if v - base > gain:
                    pick, gain = p, v - base
            trial["parts"][k] = pick
            if pick is None:
                break
            pool.remove(pick)
        dps = I.wand_stats(trial)["dps"]
        if best is None or dps > best[0]:
            best = (dps, w, [p for p in trial["parts"]])
    return (best[1], best[2]) if best else None


def housekeeping(g, rng):
    """Everything he does at home, at once -> what he did, in words."""
    p, said = g.player, []
    said += _shopping(g)
    # the wands: every body and part he has, built into the best two
    bodies = [w for w in p.wands if w] + [it for it in p.inventory if it.get("type") == "wand"]
    parts = [it for it in p.inventory if it.get("type") == "part"]
    for w in bodies:
        parts += [x for x in w["parts"] if x]
    for w in bodies:
        w["parts"] = [None] * len(w["parts"])
    p.inventory = [it for it in p.inventory if it.get("type") not in ("wand", "part")]
    ready = []
    for _ in range(2):
        b = best_wand([w for w in bodies if w not in ready], parts)
        if not b:
            break
        body, chosen = b
        body["parts"] = chosen
        for x in chosen:
            if x in parts:
                parts.remove(x)
        ready.append(body)
    old = p.wand()
    p.wands = ready + [None] * (D.WAND_SLOTS - len(ready))
    p.active = 0
    if p.wand() is not old:
        said.append(f"readied the {I.item_name(p.wand())} ({I.wand_stats(p.wand())['dps']:.0f} damage a second).")
    spare = [w for w in bodies if w not in ready] + parts
    # gear: the best of what he has, for his wand's element
    el = I.wand_stats(p.wand())["element"] if p.wand() else "arcane"
    for it in sorted([it for it in p.inventory if it.get("type") == "gear"], key=lambda it: -gear_score(it, el)):
        if gear_score(it, el) > gear_score(p.gear.get(it["slot"]), el) and it in p.inventory:
            p.equip(it)
            said.append(f"put on the {I.item_name(it)}.")
    # Mother Wren's teaching
    learned = 0
    while p.skill_points > 0:
        nid = next((n for n in SKILL_ORDER if skills.can_learn(p, n)), None)
        if not nid:
            break
        skills.learn(p, nid)
        learned += 1
    if learned:
        said.append(f"learned {learned} thing{'s' if learned > 1 else ''} from Mother Wren.")
    # the farm: harvest, water, plant; a sprinkler when there's gold to spare
    got = g.farm.harvest_all(rng)
    for k, n in list(got.items()) + list(g.farm.basket.items()):
        F.add(p.larder, k, n)
    g.farm.basket = {}
    g.farm.water_all(g.sky.day)
    planted = 0
    for i in range(len(g.farm.plots)):
        if g.farm.plots[i] is None:
            seed = next((k for k, n in sorted(p.larder.items()) if k.startswith("seed:") and n > 0), None)
            if not seed:
                break
            g.farm.plant(i, seed[5:], g.sky.day)
            F.add(p.larder, seed, -1)
            planted += 1
    if p.gold > 2500 and not g.farm.upgrades.get("sprinkler"):
        g.farm.buy("sprinkler", p)
    if got or planted:
        said.append(f"tended the farm (harvested {sum(got.values())}, planted {planted}).")
    # the hearth: cook what can be cooked (the best first), and eat the best before going down
    cooked = 0
    for k, r in sorted(F.RECIPES.items(), key=lambda kr: -(len(kr[1][2]) * 10 + kr[1][4])):
        keys = ["raw:" + x for x in r[2]]
        while F.has(p.larder, keys) and cooked < 8:
            for x in keys:
                F.add(p.larder, x, -1)
            F.add(p.larder, "cooked:" + k, 1)
            if k not in p.cookbook:
                p.cookbook.append(k)
            cooked += 1
    if cooked:
        said.append(f"cooked {cooked} meal{'s' if cooked > 1 else ''}.")
    eaten = []
    active = {b for b, _t in F.active(p.buffs)}
    for key in sorted([k for k in p.larder if k.startswith("cooked:")], key=lambda k: -F.RECIPES[k[7:]][4]):
        if len(F.active(p.buffs)) >= F.MAX_BUFFS or key[7:] in active:
            continue
        p.eat(key)
        active.add(key[7:])
        eaten.append(F.RECIPES[key[7:]][0])
    if eaten:
        said.append("ate " + ", ".join(eaten) + ".")
    # sell what's left (not the stash), and buy potions
    gold = p.gold
    for it in list(p.inventory) + spare:
        if it.get("type") in ("gear", "wand", "part"):
            if it not in p.inventory:
                p.inventory.append(it)
            shop.sell(p, it)
    if p.gold > gold:
        said.append(f"sold the rest for {p.gold - gold} gold.")
    bought = 0
    for kind, want in (("health", 6), ("mana", 4), ("return", 2)):
        while p.potions.get(kind, 0) < want and shop.buy_consumable(p, kind):
            bought += 1
    if bought:
        said.append(f"bought {bought} potion{'s' if bought > 1 else ''} and scrolls.")
    g.events.append(("save",))
    return said or ["had nothing to see to."]


def _shopping(g):
    """Old Tamsin's and Bramwell's: whatever makes his best wand stronger, or beats what he wears - with a third of
    his gold kept back."""
    p, said = g.player, []
    reach = max(g.run_floor, p.stats["deepest"])
    bodies = [w for w in p.wands if w] + [it for it in p.inventory if it.get("type") == "wand"]
    parts = [it for it in p.inventory if it.get("type") == "part"] + [x for w in bodies for x in w["parts"] if x]

    def power(bs, ps):
        b = best_wand(bs, ps)
        if not b:
            return 0.0
        return I.wand_stats(dict(b[0], parts=b[1]))["dps"]
    base = power(bodies, parts)
    for it in shop.stock("wandwright", g.seed, g.visits, reach):
        cost = I.price(it)
        if cost > p.gold * 0.66:
            continue
        nb, np_ = (bodies + [it], parts) if it["type"] == "wand" else (bodies, parts + [it])
        v = power(nb, np_)
        if v > base * 1.05 and shop.buy(p, it):
            bodies, parts, base = nb, np_, v
            said.append(f"bought the {I.item_name(it)} from Old Tamsin.")
    el = I.wand_stats(p.wand())["element"] if p.wand() else "arcane"
    for it in sorted(shop.stock("outfitter", g.seed, g.visits, reach), key=lambda it: -gear_score(it, el)):
        if I.price(it) <= p.gold * 0.66 and gear_score(it, el) > gear_score(p.gear.get(it["slot"]), el) * 1.1 and                 shop.buy(p, it):
            p.equip(it)
            said.append(f"bought and put on the {I.item_name(it)}.")
    return said
