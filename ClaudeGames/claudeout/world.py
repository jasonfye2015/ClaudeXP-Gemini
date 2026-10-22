"""Everything that changes as you play: where you are (the vault or the surface), your health and rads, what you
carry, the doors, the items still lying about, the creatures, the robot's errand, and the objectives of both parts.

Part One runs from the cryo pod to the elevator; Part Two from the hill down into Serenity Hills, to your old
house, Rustworth's pests and the bridge out of town."""
import math
import random

from . import surface as S
from . import vault as V
from .mesh import boxes_near

PLAYER_HP = 100
MAX_RADS = 70
# creatures: kind -> how they are
KINDS = {
    "roach": dict(name="Radroach", hp=3, speed=2.4, dmg=7, reach=0.8, rate=1.0, meat="meat", fly=False, w=0.95, h=0.75),
    "bloatfly": dict(name="Bloatfly", hp=2, speed=3.0, dmg=5, reach=1.0, rate=1.2, meat="meat_fly", fly=True, w=0.8, h=0.8),
    "molerat": dict(name="Mole Rat", hp=5, speed=3.4, dmg=10, reach=0.9, rate=1.1, meat="meat_rat", fly=False, w=1.1, h=0.75),
}
# aid: kind -> (name, heals, rads it gives)
AID = {"stimpak": ("Stimpak", 45, 0), "meat": ("Radroach Meat", 12, 3), "meat_fly": ("Bloatfly Meat", 10, 2),
       "meat_rat": ("Mole Rat Meat", 18, 4), "cola": ("Nuka-Cola", 8, 1), "radaway": ("RadAway", 0, -30)}
ITEM_NAMES = {"stimpak": "Stimpak", "baton": "Security Baton", "pistol": "10mm Pistol", "ammo": "10mm rounds",
              "pipboy": "Pip-Boy", "cola": "Nuka-Cola", "radaway": "RadAway", "meat": "Radroach Meat",
              "meat_fly": "Bloatfly Meat", "meat_rat": "Mole Rat Meat"}
WEAPONS = {"fists": ("Fists", 1, 1.4, 0.45), "baton": ("Security Baton", 2, 1.8, 0.55),
           "pistol": ("10mm Pistol", 4, 40.0, 0.4)}
# the objectives, in order: (part, id, text)
OBJECTIVES = [
    (1, "wake", "Get out of the cryo pod"),
    (1, "leave_cryo", "Find a way out of the cryo chamber"),
    (1, "explore", "Explore the vault"),
    (1, "defend", "Defend yourself (left click to punch)"),
    (1, "weapon", "Find a weapon"),
    (1, "security", "Find the security office"),
    (1, "unlock", "Unlock the Overseer's office (security terminal)"),
    (1, "overseer", "Reach the Overseer's office"),
    (1, "unseal", "Unseal the exit corridor (Overseer's terminal)"),
    (1, "exit_room", "Find the vault entrance"),
    (1, "pipboy", "Take the Pip-Boy from the skeleton"),
    (1, "open", "Use the Pip-Boy on the door control"),
    (1, "elevator", "Step onto the elevator and activate it"),
    (2, "surface", "Step out into the light"),
    (2, "descend", f"Follow the path down to {S.TOWN}"),
    (2, "home", "Find your old house"),
    (2, "robot", "Talk to the robot"),
    (2, "clear", "Clear the pests out of the neighbourhood"),
    (2, "report", f"Tell {S.ROBOT_NAME} the neighbourhood is clear"),
    (2, "bridge", "Head for the bridge out of town"),
    (2, "done", "Part Two complete"),
]
OBJ_INDEX = {k: i for i, (_p, k, _t) in enumerate(OBJECTIVES)}
QUESTS = {1: "Out of Time", 2: "The Neighbourhood"}


class Creature:
    def __init__(self, kind, x, z, nest, area):
        self.kind = kind
        self.x, self.z = x, z
        self.nest = nest
        self.area = area
        self.hp = KINDS[kind]["hp"]
        self.alive = True
        self.aggro = False
        self.bite_at = 0.0
        self.wobble = random.uniform(0, 6.3)
        self.hurt = 0.0
        self.side = random.choice((-1, 1))               # which way round furniture it tries first
        self.looted = False

    def to_json(self):
        return [self.kind, self.x, self.z, self.nest, self.area, self.hp, self.alive, self.aggro, self.looted]

    @classmethod
    def from_json(cls, d):
        c = cls(d[0], d[1], d[2], d[3], d[4])
        c.hp, c.alive, c.aggro, c.looted = d[5], d[6], d[7], d[8]
        return c


class World:
    def __init__(self):
        self.area = "vault"
        self.hp = PLAYER_HP
        self.rads = 0
        self.weapon = "fists"
        self.have = {"fists"}
        self.aid = {}
        self.ammo = 0
        self.pipboy = False
        self.objective = 0
        self.done = set()
        self.kills = 0
        self.time = 0.0
        self.doors = {d: 0.0 for d in V.DOORS}          # 0 closed .. 1 open
        self.unlocked = set()
        self.gear_open = False
        self.elevator = None                             # seconds since the elevator started, or None
        self.items = {"vault": dict(V.ITEMS), "surface": dict(S.ITEMS)}
        self.creatures = []
        self.nests_done = set()
        self.robot_stage = 0                             # 0 not met, 1 pests asked for, 2 sent to the bridge
        self.visited = {"vault": set(), "surface": set()}
        self.events = []                                 # (kind, detail) for the game to show and play
        self.surfaced_at = None

    # ---- objectives ----
    def goal(self):
        return OBJECTIVES[self.objective][1]

    def part(self):
        return OBJECTIVES[self.objective][0]

    def goal_text(self, key=None):
        key = key or self.goal()
        text = OBJECTIVES[OBJ_INDEX[key]][2]
        if key == "clear":
            pests = [c for c in self.creatures if c.nest == "pests"]
            text += f"  ({sum(1 for c in pests if not c.alive)}/{len(pests)})"
        return text

    def advance(self, to):
        """Move the objective on to `to` if it's further along."""
        i = OBJ_INDEX[to]
        if i > self.objective:
            for k in range(self.objective, i):
                self.done.add(OBJECTIVES[k][1])
            self.objective = i
            self.events.append(("objective", self.goal_text()))

    def target(self):
        """Where the current objective points, if anywhere."""
        g = self.goal()
        if self.area == "vault":
            return V.TARGETS.get(g)
        if g == "clear":
            alive = [c for c in self.creatures if c.nest == "pests" and c.alive]
            return (alive[0].x, alive[0].z) if alive else None
        return S.TARGETS.get(g)

    def max_hp(self):
        return PLAYER_HP - self.rads

    # ---- the ground and what's in the way ----
    def height(self, x, z):
        return S.walk_height(x, z) if self.area == "surface" else 0.0

    def solid(self, x, z):
        if self.area == "surface":
            return S.solid_cell(x, z)
        c = V.cell(int(math.floor(x)), int(math.floor(z)))
        if c == "#":
            return True
        if c == "D":
            did = V.DOOR_AT.get((int(math.floor(x)), int(math.floor(z))))
            return did is not None and self.doors[did] < 0.75
        return False

    def blocked(self, x, z, r=0.32):
        for dx in (-r, r):
            for dz in (-r, r):
                if self.solid(x + dx, z + dz):
                    return True
        grid = S.BOX_GRID if self.area == "surface" else V.BOX_GRID
        for x0, z0, x1, z1 in boxes_near(grid, x, z):
            if x0 - r < x < x1 + r and z0 - r < z < z1 + r:
                return True
        if self.area == "surface":
            for x0, z0, x1, z1 in boxes_near(S.TREE_GRID, x, z):
                if x0 - r < x < x1 + r and z0 - r < z < z1 + r:
                    return True
        return False

    def move(self, x, z, dx, dz, r=0.32):
        """Slide along whatever's in the way."""
        if not self.blocked(x + dx, z, r):
            x += dx
        if not self.blocked(x, z + dz, r):
            z += dz
        return x, z

    def line_of_sight(self, ax, az, bx, bz):
        n = int(math.hypot(bx - ax, bz - az) * 4) + 1
        for k in range(1, n):
            t = k / n
            if self.solid(ax + (bx - ax) * t, az + (bz - az) * t):
                return False
        return True

    # ---- the clock ----
    def update(self, dt, px, pz, now):
        self.time += dt
        cx, cz = int(math.floor(px)), int(math.floor(pz))
        self.visited[self.area].add((cx, cz))
        if self.area == "vault":
            self._update_vault(dt, px, pz, cx, cz)
        else:
            self._update_surface(dt, px, pz, cx, cz)
        self._update_creatures(dt, px, pz, now)

    def _update_vault(self, dt, px, pz, cx, cz):
        room = V.room_at(cx, cz)
        for did, (cells, kind) in V.DOORS.items():
            if kind == "gear":
                want = 1.0 if self.gear_open else 0.0
            else:
                near = any(abs(px - (x + 0.5)) < 2.4 and abs(pz - (z + 0.5)) < 2.4 for x, z in cells)
                want = 1.0 if near and (kind == "auto" or did in self.unlocked) else 0.0
                if near and want == 0.0 and self.doors[did] == 0.0 and kind == "locked":
                    self._locked_hint(did)
            cur = self.doors[did]
            speed = dt / (6.0 if kind == "gear" else 0.45)
            new = min(1.0, cur + speed) if want > cur else max(0.0, cur - speed)
            if new != cur:
                if cur == 0.0 and kind != "gear":
                    self.events.append(("door", did))
                self.doors[did] = new
                if kind == "gear" and new >= 1.0:
                    self.advance("elevator")
        if room == "corr1":
            self.advance("explore")
        if room == "security" and "overseer" not in self.unlocked:
            self.advance("unlock")
        if room == "overseer" and "exit_path" not in self.unlocked:
            self.advance("unseal")
        if room == "exit" and not self.pipboy:
            self.advance("pipboy")
        self._nests(V.NESTS, cx, cz)
        if "corr1" in self.nests_done and self.objective < OBJ_INDEX["weapon"] \
                and all(not c.alive for c in self.creatures if c.nest == "corr1"):
            self.advance("weapon")
        if self.elevator is not None:
            self.elevator += dt
            if self.elevator > 7.0:
                self.go_surface()

    def _update_surface(self, dt, px, pz, cx, cz):
        self._nests(S.NESTS, cx, cz)
        g = self.goal()
        if g == "surface" and math.hypot(px - S.HILL[0], pz - S.HILL[1]) > 7:
            self.advance("descend")
        if g == "descend" and px > 42 and pz > 40:
            self.advance("home")
        if g == "home" and math.hypot(px - S.TARGETS["home"][0], pz - S.TARGETS["home"][1]) < 7:
            self.advance("robot")
        if g == "clear" and all(not c.alive for c in self.creatures if c.nest == "pests"):
            self.advance("report")
        if S.cell(cx, cz) == "b" and px >= S.BRIDGE_END_X and g != "done":
            self.advance("done")
            self.events.append(("end", None))

    def _nests(self, nests, cx, cz):
        for name, (x0, z0, x1, z1), spots in nests:
            if name not in self.nests_done and x0 <= cx <= x1 and z0 <= cz <= z1:
                self.nests_done.add(name)
                for kind, sx, sz in spots:
                    self.creatures.append(Creature(kind, sx, sz, name, self.area))
                self.events.append(("creatures", [k for k, _x, _z in spots]))
                if self.area == "vault" and self.objective < OBJ_INDEX["defend"]:
                    self.advance("defend")

    def _update_creatures(self, dt, px, pz, now):
        for c in self.creatures:
            if not c.alive or c.area != self.area:
                continue
            k = KINDS[c.kind]
            d = math.hypot(px - c.x, pz - c.z)
            if not c.aggro and d < 14 and self.line_of_sight(c.x, c.z, px, pz):
                c.aggro = True
                self.events.append(("aggro", c.kind))
            if not c.aggro:
                continue
            if d > k["reach"]:
                step = k["speed"] * dt
                ux, uz = (px - c.x) / d, (pz - c.z) / d
                nx, nz = self.move(c.x, c.z, ux * step, uz * step, 0.25)
                if math.hypot(nx - c.x, nz - c.z) < step * 0.4:       # something in the way: go round it
                    sx, sz = -uz * c.side, ux * c.side
                    nx, nz = self.move(c.x, c.z, (ux * 0.3 + sx) * step, (uz * 0.3 + sz) * step, 0.25)
                    if math.hypot(nx - c.x, nz - c.z) < step * 0.4:
                        c.side = -c.side
                c.x, c.z = nx, nz
            elif now - c.bite_at > k["rate"]:
                c.bite_at = now
                self.hp -= k["dmg"]
                self.events.append(("bite", c.kind))
            c.hurt = max(0.0, c.hurt - dt)

    def _locked_hint(self, did):
        key = f"hint_{did}"
        if key not in self.done:
            self.done.add(key)
            self.events.append(("say", "Locked. A terminal somewhere controls this door."
                                if did == "overseer" else "Sealed from the Overseer's office."))

    def go_surface(self):
        """Up the elevator and out: Part Two."""
        self.area = "surface"
        self.elevator = None
        self.advance("surface")
        self.events.append(("surface", None))

    # ---- doing things ----
    def attack(self, px, pz, yaw, now):
        """Swing or shoot at what's in front of you. Returns what happened."""
        name, dmg, reach, rate = WEAPONS[self.weapon]
        if self.weapon == "pistol":
            if self.ammo <= 0:
                return "empty"
            self.ammo -= 1
        fx, fz = -math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))
        best, best_d = None, reach
        for c in self.creatures:
            if not c.alive or c.area != self.area:
                continue
            dx, dz = c.x - px, c.z - pz
            d = math.hypot(dx, dz)
            if d > reach or d == 0:
                continue
            along = dx * fx + dz * fz
            across = abs(dx * fz - dz * fx)
            if along > 0 and across < (0.6 if self.weapon != "pistol" else 0.35 + d * 0.03) and d < best_d \
                    and self.line_of_sight(px, pz, c.x, c.z):
                best, best_d = c, d
        if best is None:
            return "miss"
        best.hp -= dmg
        best.hurt = 0.25
        best.aggro = True
        if best.hp <= 0:
            best.alive = False
            self.kills += 1
            return "kill"
        return "hit"

    def interact(self, px, pz, yaw):
        """E: pick something up, loot a corpse, use a terminal or a control, talk. Returns (kind, detail) or None."""
        fx, fz = -math.sin(math.radians(yaw)), -math.cos(math.radians(yaw))

        def facing(x, z, reach):
            dx, dz = x - px, z - pz
            d = math.hypot(dx, dz)
            return d < reach and (dx * fx + dz * fz) / max(d, 0.01) > 0.5

        items = self.items[self.area]
        for iid, (kind, x, z) in list(items.items()):
            if facing(x, z, 1.9):
                del items[iid]
                return self.pick_up(kind)
        for c in self.creatures:
            if not c.alive and not c.looted and c.area == self.area and facing(c.x, c.z, 1.9):
                c.looted = True
                meat = KINDS[c.kind]["meat"]
                self.aid[meat] = self.aid.get(meat, 0) + 1
                return ("loot", meat)
        if self.area == "vault":
            for tid, (x, z, _title, _lines) in V.TERMINALS.items():
                if facing(x, z, 2.0):
                    return ("terminal", tid)
            for cid, (x, z) in V.CONTROLS.items():
                if facing(x, z, 2.2):
                    return self.use_control(cid, px, pz)
            if facing(V.SKELETON[0], V.SKELETON[1], 1.9) and "pipboy" in items:
                del items["pipboy"]
                return self.pick_up("pipboy")
        else:
            if facing(S.ROBOT[0], S.ROBOT[1], 2.8):
                return ("talk", self.talk())
        return None

    def pick_up(self, kind):
        if kind in AID:
            self.aid[kind] = self.aid.get(kind, 0) + 1
        elif kind == "ammo":
            self.ammo += 12
        elif kind == "baton":
            self.have.add("baton")
            self.weapon = "baton"
            self.advance("security")
        elif kind == "pistol":
            self.have.add("pistol")
            self.weapon = "pistol"
            self.ammo += 8
            if "overseer" not in self.unlocked:
                self.advance("unlock")
        elif kind == "pipboy":
            self.pipboy = True
            self.advance("open")
        return ("pickup", kind)

    def eat(self, kind):
        """Use an aid item from the Pip-Boy. Returns True if it did something."""
        if self.aid.get(kind, 0) <= 0:
            return False
        name, heal, rads = AID[kind]
        if kind == "radaway" and self.rads <= 0:
            return False
        if heal and self.hp >= self.max_hp() and rads >= 0:
            return False
        self.aid[kind] -= 1
        self.rads = max(0, min(MAX_RADS, self.rads + rads))
        self.hp = max(1, min(self.max_hp(), self.hp + heal))
        return True

    def use_stimpak(self):
        return self.eat("stimpak")

    def use_terminal(self, tid):
        """The terminal's option was chosen. Returns a message."""
        if tid == "security":
            if "overseer" in self.unlocked:
                return "Overseer's office: already unlocked."
            self.unlocked.add("overseer")
            self.advance("overseer")
            return "Overseer's office: UNLOCKED."
        if tid == "overseer":
            if "exit_path" in self.unlocked:
                return "Exit corridor: already open."
            self.unlocked.add("exit_path")
            self.advance("exit_room")
            return "Exit corridor: UNSEALED."
        return ""

    def use_control(self, cid, px, pz):
        if cid == "door":
            if self.gear_open:
                return ("say", "The door is open.")
            if not self.pipboy:
                return ("say", "A Pip-Boy is needed to open the vault door.")
            self.gear_open = True
            return ("gear", None)
        if cid == "elevator":
            if not self.gear_open:
                return ("say", "Nothing happens.")
            if not self.on_elevator(px, pz):
                return ("say", "Stand on the platform first.")
            if self.elevator is None:
                self.elevator = 0.0
                return ("elevator", None)
        return None

    def on_elevator(self, px, pz):
        x0, z0, x1, z1 = V.ELEVATOR
        return x0 <= px < x1 + 1 and z0 <= pz < z1 + 1

    # ---- the robot ----
    def talk(self):
        """Which of Rustworth's lines to open with."""
        if self.robot_stage == 0:
            return "start"
        if self.robot_stage == 1:
            return "cleared" if all(not c.alive for c in self.creatures if c.nest == "pests") else "progress"
        return "after"

    def choose(self, nxt):
        """A choice was made: the next node, or None when the talk is over (with its effect done)."""
        if nxt == "end:clear":
            self.robot_stage = 1
            for kind, x, z in S.PESTS:
                self.creatures.append(Creature(kind, x, z, "pests", "surface"))
            self.advance("clear")
            self.events.append(("creatures", ["pests"]))
            return None
        if nxt == "end:bridge":
            self.robot_stage = 2
            self.advance("bridge")
            return None
        if nxt == "end":
            return None
        return nxt

    # ---- saving ----
    def to_json(self):
        return {"area": self.area, "hp": self.hp, "rads": self.rads, "weapon": self.weapon, "have": sorted(self.have),
                "aid": self.aid, "ammo": self.ammo, "pipboy": self.pipboy, "objective": self.objective,
                "done": sorted(self.done), "kills": self.kills, "time": self.time, "doors": self.doors,
                "unlocked": sorted(self.unlocked), "gear_open": self.gear_open, "elevator": self.elevator,
                "items": {a: {k: list(v) for k, v in d.items()} for a, d in self.items.items()},
                "creatures": [c.to_json() for c in self.creatures], "nests_done": sorted(self.nests_done),
                "robot_stage": self.robot_stage, "visited": {a: sorted(v) for a, v in self.visited.items()}}

    @classmethod
    def from_json(cls, d):
        w = cls()
        w.area = d.get("area", "vault")
        w.hp = d.get("hp", PLAYER_HP)
        w.rads = d.get("rads", 0)
        w.weapon = d.get("weapon", "fists")
        w.have = set(d.get("have", ["fists"]))
        w.aid = {k: int(v) for k, v in d.get("aid", {}).items()}
        w.ammo = d.get("ammo", 0)
        w.pipboy = d.get("pipboy", False)
        w.objective = d.get("objective", 0)
        w.done = set(d.get("done", []))
        w.kills = d.get("kills", 0)
        w.time = d.get("time", 0.0)
        w.doors = {k: float(d.get("doors", {}).get(k, 0.0)) for k in V.DOORS}
        w.unlocked = set(d.get("unlocked", []))
        w.gear_open = d.get("gear_open", False)
        w.elevator = d.get("elevator")
        for area in ("vault", "surface"):
            if area in d.get("items", {}):
                w.items[area] = {k: tuple(v) for k, v in d["items"][area].items()}
        w.creatures = [Creature.from_json(c) for c in d.get("creatures", [])]
        w.nests_done = set(d.get("nests_done", []))
        w.robot_stage = d.get("robot_stage", 0)
        for area in ("vault", "surface"):
            w.visited[area] = {tuple(c) for c in d.get("visited", {}).get(area, [])}
        return w
