"""Claude Shelter's rules: the vault (rooms on a grid of floors), its dwellers and their S.P.E.C.I.A.L., power, food
and water, incidents, babies, the radio, the wasteland, storage, objectives and lunchboxes.

No Qt in here. A vault is plain data, so it saves as JSON; the window calls update(dt) and draws what it finds."""
import random
import time

CELLS = 25                      # cells across a floor
FLOORS = 25
SEG = 3                         # cells in one room segment (an elevator is 1)
STAT_NAMES = ["Strength", "Perception", "Endurance", "Charisma", "Intelligence", "Agility", "Luck"]
LEVEL_MULT = (1.0, 1.4, 1.8)

ROOMS = {
    "door": dict(name="Vault Door", emoji="⚙️", stat=None, cost=500, unlock=0, kind="door", colour="#5A6470"),
    "elevator": dict(name="Elevator", emoji="🛗", stat=None, cost=100, unlock=0, kind="elevator", colour="#4A4F55"),
    "living": dict(name="Living Quarters", emoji="🛏️", stat=3, cost=100, unlock=0, kind="living", colour="#8C6A4A"),
    "power": dict(name="Power Generator", emoji="⚡", stat=0, cost=100, unlock=0, kind="produce", produce="power",
                  colour="#B8922E"),
    "diner": dict(name="Diner", emoji="🍔", stat=5, cost=100, unlock=0, kind="produce", produce="food",
                  colour="#B5603A"),
    "water": dict(name="Water Treatment", emoji="💧", stat=1, cost=100, unlock=0, kind="produce", produce="water",
                  colour="#3A7FB0"),
    "storage": dict(name="Storage Room", emoji="📦", stat=2, cost=300, unlock=12, kind="storage", colour="#6E6A5E"),
    "medbay": dict(name="Medbay", emoji="💊", stat=4, cost=400, unlock=14, kind="produce", produce="stimpak",
                   colour="#A9B8BE"),
    "science": dict(name="Science Lab", emoji="☢️", stat=4, cost=400, unlock=16, kind="produce", produce="radaway",
                    colour="#5E8F45"),
    "radio": dict(name="Radio Studio", emoji="📻", stat=3, cost=600, unlock=20, kind="radio", colour="#7A4FA0"),
    "weight": dict(name="Weight Room", emoji="🏋️", stat=0, cost=1000, unlock=24, kind="training", colour="#5E5E70"),
    "athletics": dict(name="Athletics Room", emoji="🏃", stat=5, cost=1000, unlock=26, kind="training",
                      colour="#4F7A6A"),
    "armory": dict(name="Armory", emoji="🎯", stat=1, cost=1000, unlock=28, kind="training", colour="#6A5A44"),
    "classroom": dict(name="Classroom", emoji="📚", stat=4, cost=1200, unlock=30, kind="training", colour="#4A5E8A"),
    "fitness": dict(name="Fitness Room", emoji="🤸", stat=2, cost=1500, unlock=32, kind="training", colour="#8A4A5E"),
    "lounge": dict(name="Lounge", emoji="🍸", stat=3, cost=1500, unlock=35, kind="training", colour="#8A6A2E"),
    "game": dict(name="Game Room", emoji="🎲", stat=6, cost=1500, unlock=40, kind="training", colour="#3E7A3A"),
    "nuka": dict(name="Nuka-Cola Bottler", emoji="🥤", stat=2, cost=3000, unlock=30, kind="produce", produce="nuka",
                 colour="#A8303E"),
}
BUILD_ORDER = ["elevator", "living", "power", "diner", "water", "storage", "medbay", "science", "radio", "weight",
               "athletics", "armory", "classroom", "fitness", "lounge", "game", "nuka"]
RESOURCES = {"power": ("⚡", "Power"), "food": ("🍔", "Food"), "water": ("💧", "Water"),
             "stimpak": ("💊", "Stimpaks"), "radaway": ("☢️", "RadAway"), "nuka": ("🥤", "Nuka-Cola")}

# (name, damage low, damage high, rarity 0 common / 1 rare / 2 legendary)
WEAPONS = [("BB Gun", 2, 3, 0), (".32 Pistol", 2, 4, 0), ("Rusty Hunting Rifle", 3, 5, 0), ("10mm Pistol", 2, 5, 0),
           ("Sawed-off Shotgun", 4, 8, 0), ("Laser Pistol", 3, 7, 0), ("Hunting Rifle", 5, 9, 1),
           ("Assault Rifle", 6, 10, 1), ("Plasma Pistol", 7, 12, 1), ("Laser Rifle", 8, 13, 1),
           ("Combat Shotgun", 9, 14, 1), ("Plasma Rifle", 12, 18, 2), ("Gatling Laser", 14, 20, 2),
           ("Fat Man", 20, 30, 2)]
WEAPON = {w[0]: w for w in WEAPONS}
# (name, {stat: bonus}, rarity, colour)
OUTFITS = [("Wasteland Gear", {2: 1, 5: 1}, 0, "#8A7A5A"), ("Lab Coat", {4: 2}, 0, "#E8E8E0"),
           ("Mechanic Jumpsuit", {0: 2}, 0, "#6A7A8A"), ("Formal Wear", {3: 2}, 0, "#2A2A30"),
           ("Leather Armor", {2: 2}, 0, "#7A5030"), ("Military Fatigues", {0: 2, 2: 1}, 1, "#4E5E3A"),
           ("Sheriff's Duster", {1: 2, 3: 1}, 1, "#8A6040"), ("Lucky Formal Wear", {6: 3}, 1, "#3A2A5A"),
           ("Expert Lab Coat", {4: 3, 1: 1}, 1, "#D8E8F0"), ("Battle Armor", {0: 2, 1: 2, 2: 2}, 2, "#5A5048"),
           ("Power Armor", {0: 3, 2: 3}, 2, "#7A7A6A"), ("Overseer's Uniform", {3: 3, 4: 3}, 2, "#2E4E8A")]
OUTFIT = {o[0]: o for o in OUTFITS}
RARITY = ("Common", "Rare", "Legendary")

INCIDENTS = {
    "fire": dict(name="Fire", emoji="🔥", hp=40, dmg=1.0, spread=True, caps=30, pop=0),
    "roaches": dict(name="Radroaches", emoji="🪳", hp=50, dmg=0.9, spread=True, caps=40, pop=0),
    "molerats": dict(name="Mole Rats", emoji="🐀", hp=80, dmg=1.5, spread=True, caps=60, pop=14),
    "raiders": dict(name="Raiders", emoji="💀", hp=110, dmg=2.0, moves=True, caps=100, pop=10),
    "deathclaws": dict(name="Deathclaws", emoji="🦖", hp=360, dmg=5.0, moves=True, caps=300, pop=40),
}

FIRST_M = ["Abe", "Arlo", "Ben", "Carl", "Dale", "Eli", "Floyd", "Gus", "Hank", "Ike", "Jack", "Ken", "Lou", "Mack",
           "Ned", "Otis", "Pete", "Ray", "Sam", "Ted", "Vic", "Walt", "Wes", "Cliff", "Roy", "Hal", "Dewey", "Earl",
           "Monty", "Buck", "Rex", "Stan", "Milo", "Ollie", "Rusty"]
FIRST_F = ["Ada", "Bea", "Cora", "Dot", "Edie", "Faye", "Gail", "Hazel", "Iris", "June", "Kay", "Lola", "Mae", "Nell",
           "Opal", "Peg", "Rose", "Sue", "Tess", "Vera", "Wren", "Joan", "Lucy", "Mabel", "Ruby", "Stella", "Velma",
           "Ida", "Pearl", "Daisy", "Hattie", "Polly", "Greta", "Nora", "Ivy"]
LAST = ["Adams", "Baker", "Carter", "Dawson", "Ellis", "Fisher", "Garcia", "Hayes", "Irving", "Jensen", "Keller",
        "Lopez", "Morgan", "Nash", "Owens", "Parker", "Quinn", "Reyes", "Stone", "Turner", "Vance", "Walker", "Young",
        "Booker", "Calloway", "Doyle", "Fontaine", "Harlow", "Kowalski", "Mercer", "Novak", "Okafor", "Patel",
        "Rinaldi", "Sato", "Thorne", "Whitlock"]
SKIN = ["#F2D2B6", "#E8BE98", "#D4A27A", "#B07C55", "#8C5A3A", "#6A4028"]
HAIR = ["#2A1E16", "#5A3A22", "#8A5A2A", "#C89A4A", "#E8D27A", "#A83A22", "#888888", "#E8E8E8"]
PLACES = ["an abandoned gas station", "a collapsed overpass", "a crater full of glowing goo", "a burned-out diner",
          "a Red Rocket truck stop", "a derelict school bus", "a raider camp (empty, thankfully)", "an old drive-in",
          "a radio tower", "a flooded subway entrance", "a trailer park", "a pre-war supermarket", "a ruined church",
          "a dried-up lake bed", "a crashed vertibird", "a super-duper mart", "a junkyard", "a farmhouse"]
CREATURES = [("a radroach", 4), ("a mole rat", 6), ("a feral ghoul", 9), ("a pack of wild dogs", 8),
             ("a raider", 10), ("a radscorpion", 14), ("a super mutant", 18), ("a yao guai", 20),
             ("a deathclaw", 30)]
LEGENDS = [("Sarge Calloway", "M", [9, 6, 8, 4, 3, 6, 5]), ("Doc Fontaine", "F", [3, 7, 4, 6, 10, 5, 6]),
           ("Lucky Novak", "M", [4, 5, 4, 7, 4, 6, 10]), ("Ace Harlow", "F", [5, 9, 5, 5, 6, 9, 6]),
           ("Big Mae Kowalski", "F", [10, 4, 9, 5, 3, 4, 5]), ("Smooth Rinaldi", "M", [4, 5, 5, 10, 6, 5, 7])]

OBJECTIVES = [("Collect {n} Food", "food", [100, 300, 800]), ("Collect {n} Water", "water", [100, 300, 800]),
              ("Collect {n} Power", "power", [100, 300, 800]), ("Build {n} rooms", "built", [2, 4, 8]),
              ("Upgrade {n} rooms", "upgrades", [1, 3, 5]), ("Rush {n} rooms successfully", "rush_ok", [1, 3, 5]),
              ("Defeat {n} incidents", "incidents", [2, 5, 10]), ("Have {n} babies born", "births", [1, 2, 4]),
              ("Level up dwellers {n} times", "levelups", [5, 10, 25]),
              ("Explore the wasteland for {n} minutes", "explore_min", [5, 15, 30]),
              ("Earn {n} caps", "caps", [200, 600, 2000]), ("Train {n} S.P.E.C.I.A.L. points", "trained", [2, 5, 10]),
              ("Equip {n} weapons or outfits", "equips", [1, 3, 6]),
              ("Welcome {n} new dwellers", "arrivals", [2, 5, 10]),
              ("Collect {n} Stimpaks", "stimpak", [3, 10, 25])]


def width(room):
    return 1 if room["type"] == "elevator" else SEG * room["segs"]


def xp_needed(level):
    return 50 + level * 40


class Vault:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.number = self.rng.randint(100, 999)
        self.time = 0.0
        self.next_id = 1
        self.caps = 1000
        self.res = {"power": 60.0, "food": 60.0, "water": 60.0}
        self.stimpaks = 3
        self.radaway = 2
        self.rooms = []
        self.dwellers = []
        self.items = []
        self.msgs = []
        self.counters = {}
        self.objectives = []
        self.lunchboxes = 1
        self.door_hp = 100.0
        self.next_incident = 300.0
        self.next_arrival = 120.0
        self.radio = 0.0
        self.saved_at = time.time()
        self._build_start()
        self._rebuild()
        for _ in range(6):
            self.new_dweller(at_door=False)
        for d, room in zip(self.dwellers, [r for r in self.rooms if r["type"] in ("power", "diner", "water")] * 2):
            self.assign(d, room, walk=False)
        for _ in range(3):
            self._new_objective()

    # ---- saving ----
    def to_json(self):
        d = {k: v for k, v in self.__dict__.items() if k not in ("rng", "grid", "by_id")}
        st = self.rng.getstate()
        d["rng"] = [st[0], list(st[1]), st[2]]
        d["saved_at"] = time.time()
        return d

    @classmethod
    def from_json(cls, d):
        v = cls.__new__(cls)
        d = dict(d)
        st = d.pop("rng")
        v.__dict__.update(d)
        v.rng = random.Random()
        v.rng.setstate((st[0], tuple(st[1]), st[2]))
        v._rebuild()
        v.catch_up(time.time() - v.saved_at)
        return v

    def catch_up(self, seconds):
        """Time spent away: the wasteland, babies and growing children carry on (gently - no disasters)."""
        seconds = max(0.0, min(3600.0, seconds))
        step = max(1.0, seconds / 600)
        for _ in range(int(seconds / step)):
            self.update(step, offline=True)

    # ---- ids, messages ----
    def _id(self):
        self.next_id += 1
        return self.next_id

    def say(self, text, kind="info"):
        self.msg_n = getattr(self, "msg_n", 0) + 1
        self.msgs.append({"n": self.msg_n, "t": self.time, "text": text, "kind": kind})
        del self.msgs[:-60]

    def count(self, key, n=1):
        self.counters[key] = self.counters.get(key, 0) + n

    # ---- the grid ----
    def _build_start(self):
        self._add_room("door", 0, 0)
        for f in range(3):
            self._add_room("elevator", f, 3)
        self._add_room("living", 0, 4)
        self._add_room("power", 1, 4)
        self._add_room("diner", 1, 7)
        self._add_room("water", 2, 4)

    def _add_room(self, kind, floor, cell, segs=1, level=1):
        r = {"id": self._id(), "type": kind, "floor": floor, "cell": cell, "segs": segs, "level": level,
             "prog": 0.0, "ready": 0.0, "inc": None, "heat": 0.0, "rom": 0.0, "train": {}}
        self.rooms.append(r)
        return r

    def _rebuild(self):
        self.grid = {}
        self.by_id = {r["id"]: r for r in self.rooms}
        for r in self.rooms:
            for c in range(r["cell"], r["cell"] + width(r)):
                self.grid[(r["floor"], c)] = r["id"]

    def room(self, rid):
        return self.by_id.get(rid)

    def room_at(self, floor, cell):
        rid = self.grid.get((floor, cell))
        return self.room(rid) if rid else None

    def door(self):
        return next(r for r in self.rooms if r["type"] == "door")

    def free(self, floor, cell, w):
        if floor < 0 or floor >= FLOORS or cell < 0 or cell + w > CELLS:
            return False
        return all((floor, c) not in self.grid for c in range(cell, cell + w))

    def can_place(self, kind, floor, cell):
        w = 1 if kind == "elevator" else SEG
        if not self.free(floor, cell, w):
            return False
        side = (floor, cell - 1) in self.grid or (floor, cell + w) in self.grid
        if kind == "elevator":
            above = self.room_at(floor - 1, cell)
            below = self.room_at(floor + 1, cell)
            if (above and above["type"] == "elevator") or (below and below["type"] == "elevator"):
                return True
            return side
        return side

    def placements(self, kind):
        w = 1 if kind == "elevator" else SEG
        out = []
        deepest = max(r["floor"] for r in self.rooms)
        for f in range(0, min(FLOORS, deepest + 2)):
            for c in range(0, CELLS - w + 1):
                if self.can_place(kind, f, c):
                    out.append((f, c))
        return out

    def cost(self, kind):
        info = ROOMS[kind]
        if kind == "elevator":
            return info["cost"]
        n = sum(r["segs"] for r in self.rooms if r["type"] == kind)
        return info["cost"] + 25 * n

    def unlocked(self, kind):
        return self.population() >= ROOMS[kind]["unlock"]

    def build(self, kind, floor, cell):
        if not self.unlocked(kind):
            return f"Needs {ROOMS[kind]['unlock']} dwellers"
        price = self.cost(kind)
        if self.caps < price:
            return "Not enough caps"
        if not self.can_place(kind, floor, cell):
            return "Can't build there"
        self.caps -= price
        r = self._add_room(kind, floor, cell)
        self._rebuild()
        if kind != "elevator":
            self._merge(r)
        self.count("built")
        self.say(f"Built a {ROOMS[kind]['name']}.")
        return None

    def _merge(self, r):
        """Rooms of a kind and level side by side join up, three segments at most."""
        changed = True
        while changed:
            changed = False
            for other in list(self.rooms):
                if other is r or other["type"] != r["type"] or other["level"] != r["level"]:
                    continue
                if other["floor"] != r["floor"] or other["segs"] + r["segs"] > 3:
                    continue
                if other["cell"] + width(other) == r["cell"] or r["cell"] + width(r) == other["cell"]:
                    keep, gone = (other, r) if other["cell"] < r["cell"] else (r, other)
                    keep["segs"] += gone["segs"]
                    keep["prog"] = max(keep["prog"], gone["prog"])
                    keep["ready"] += gone["ready"]
                    for d in self.dwellers:
                        if d["room"] == gone["id"]:
                            d["room"] = keep["id"]
                    self.rooms.remove(gone)
                    r = keep
                    changed = True
                    break
        self._rebuild()
        return r

    def upgrade_cost(self, r):
        if r["type"] in ("elevator",) or r["level"] >= 3:
            return None
        base = ROOMS[r["type"]]["cost"]
        return int(base * (4 if r["level"] == 1 else 12) * (0.6 + 0.4 * r["segs"]))

    def upgrade(self, r):
        price = self.upgrade_cost(r)
        if price is None:
            return "Fully upgraded"
        if self.caps < price:
            return "Not enough caps"
        self.caps -= price
        r["level"] += 1
        if r["type"] == "door":
            self.door_hp = self.door_max()
        self.count("upgrades")
        self.say(f"{ROOMS[r['type']]['name']} upgraded to level {r['level']}.")
        if r["type"] not in ("door", "elevator"):
            self._merge(r)
        return None

    def destroy(self, r):
        if r["type"] == "door":
            return "The vault door stays"
        if any(d["room"] == r["id"] or self.located(d) is r for d in self.dwellers
               if d["state"] not in ("exploring", "returning", "dead_out")):
            return "Move everyone out first"
        if r["inc"]:
            return "Deal with the incident first"
        self.rooms.remove(r)
        self._rebuild()
        if not self._connected():
            self.rooms.append(r)
            self._rebuild()
            return "That would cut the vault off"
        self.say(f"Destroyed a {ROOMS[r['type']]['name']}.")
        return None

    def _connected(self):
        start = (0, self.door()["cell"])
        seen = {start}
        todo = [start]
        while todo:
            node = todo.pop()
            for nxt in self._neighbours(node):
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return all(k in seen for k in self.grid)

    def _neighbours(self, node):
        f, c = node
        out = []
        for dc in (-1, 1):
            if (f, c + dc) in self.grid:
                out.append((f, c + dc))
        r = self.room_at(f, c)
        if r and r["type"] == "elevator":
            for df in (-1, 1):
                o = self.room_at(f + df, c)
                if o and o["type"] == "elevator":
                    out.append((f + df, c))
        return out

    def path(self, start, goal):
        """Cells to walk through, breadth first (across a floor, up and down the elevators)."""
        if start == goal:
            return [goal]
        prev = {start: None}
        todo = [start]
        i = 0
        while i < len(todo):
            node = todo[i]
            i += 1
            if node == goal:
                break
            for nxt in self._neighbours(node):
                if nxt not in prev:
                    prev[nxt] = node
                    todo.append(nxt)
        if goal not in prev:
            return None
        out = []
        node = goal
        while node is not None:
            out.append(node)
            node = prev[node]
        return out[::-1]

    # ---- dwellers ----
    def population(self):
        return sum(1 for d in self.dwellers if d["state"] not in ("dead", "dead_out"))

    def capacity(self):
        mult = (8, 10, 12)
        return sum(mult[r["level"] - 1] * r["segs"] for r in self.rooms if r["type"] == "living")

    def new_dweller(self, at_door=True, sex=None, special=None, name=None, child=0.0, parents=(), legendary=False):
        rng = self.rng
        sex = sex or rng.choice("MF")
        if name is None:
            name = f"{rng.choice(FIRST_M if sex == 'M' else FIRST_F)} {rng.choice(LAST)}"
        if special is None:
            special = [rng.randint(1, 3) for _ in range(7)]
            special[rng.randrange(7)] += rng.randint(0, 2)
        door = self.door()
        d = {"id": self._id(), "name": name, "sex": sex, "skin": rng.choice(SKIN), "hair": rng.choice(HAIR),
             "style": rng.randrange(4), "special": list(special), "level": 1, "xp": 0.0, "hp": 105.0, "rad": 0.0,
             "happy": 60.0, "room": None, "outfit": None, "weapon": None, "x": door["cell"] + 1.5,
             "y": float(door["floor"]), "path": [], "then": None, "state": "idle", "child": child, "preg": 0.0,
             "cool": 0.0, "parents": list(parents), "ex": None, "stim": 0, "radaway": 0, "train": 0.0,
             "wander": 0.0, "wx": None, "face": 1, "legend": legendary, "fight": 0.0, "partner": None}
        if not at_door:
            d["x"] = door["cell"] + 0.5 + rng.random() * 2
        d["hp"] = self.max_hp(d)
        self.dwellers.append(d)
        return d

    def dweller(self, did):
        for d in self.dwellers:
            if d["id"] == did:
                return d
        return None

    def stat(self, d, i):
        bonus = OUTFIT[d["outfit"]][1].get(i, 0) if d["outfit"] else 0
        return d["special"][i] + bonus

    def max_hp(self, d):
        return 105 + (d["level"] - 1) * (2.5 + 0.5 * self.stat(d, 2))

    def hp_cap(self, d):
        return max(1.0, self.max_hp(d) - d["rad"])

    def adult(self, d):
        return d["child"] <= 0

    def located(self, d):
        """The room a dweller is standing in (or None while walking between or out in the wasteland)."""
        if d["state"] in ("exploring", "returning", "dead_out"):
            return None
        return self.room_at(int(round(d["y"])), int(d["x"]))

    def present(self, room):
        """Who's actually in the room, at work."""
        return [d for d in self.dwellers if d["room"] == room["id"] and d["state"] == "idle" and self.adult(d)]

    def assigned(self, room):
        return [d for d in self.dwellers if d["room"] == room["id"] and d["state"] in ("idle", "walking")]

    def room_cap(self, room):
        if room["type"] == "elevator":
            return 0
        if room["type"] == "door":
            return 2
        return 2 * room["segs"]

    def best_stat(self, d):
        vals = [self.stat(d, i) for i in range(7)]
        return vals.index(max(vals))

    def ideal(self, d, room):
        st = ROOMS[room["type"]]["stat"]
        if st is None:
            return False
        return self.stat(d, st) >= max(self.stat(d, i) for i in range(7))

    def assign(self, d, room, walk=True):
        if d["state"] in ("dead", "dead_out", "exploring", "returning"):
            return "They can't go there now"
        if not self.adult(d) and room["type"] != "living":
            return "Children can only stay in the Living Quarters"
        if room["type"] == "elevator":
            return "That's an elevator"
        if d["room"] == room["id"]:
            return None
        if len(self.assigned(room)) >= self.room_cap(room):
            return f"The {ROOMS[room['type']]['name']} is full"
        d["room"] = room["id"]
        d["train"] = 0.0
        if self.ideal(d, room):
            d["happy"] = min(100.0, d["happy"] + 5)
        if walk:
            self.walk_to(d, room)
        else:
            d["x"] = room["cell"] + 0.5 + self.rng.random() * (width(room) - 1)
            d["y"] = float(room["floor"])
            d["state"] = "idle"
        return None

    def walk_to(self, d, room, then=None):
        sx = int(min(CELLS - 1, max(0, d["x"])))
        sy = int(round(d["y"]))
        if (sy, sx) not in self.grid:                # (somewhere odd: step back onto the grid)
            here = self.door()
            sx, sy = here["cell"], here["floor"]
            d["x"] = sx + 0.5
        d["y"] = float(sy)
        d["wx"] = None
        tx = room["cell"] + self.rng.randrange(width(room))
        cells = self.path((sy, sx), (room["floor"], tx))
        if not cells:
            d["x"], d["y"] = tx + 0.5, float(room["floor"])
            d["path"] = [[tx + 0.5, float(room["floor"])]]
        else:
            d["path"] = [[sx + 0.5, float(sy)]] + [[c + 0.5, float(f)] for f, c in cells[1:]]
        d["state"] = "walking"
        d["then"] = then

    def _move(self, d, dt):
        speed = 3.0 * dt
        while d["path"] and speed > 0:
            tx, ty = d["path"][0]
            dx, dy = tx - d["x"], ty - d["y"]
            dist = abs(dx) + abs(dy)
            if dist <= speed:
                d["x"], d["y"] = tx, ty
                d["path"].pop(0)
                speed -= dist
            else:
                if abs(dy) > 1e-6:
                    d["y"] += speed if dy > 0 else -speed
                else:
                    d["x"] += speed if dx > 0 else -speed
                    d["face"] = 1 if dx > 0 else -1
                speed = 0
        if not d["path"]:
            d["state"] = "idle"
            then = d["then"]
            d["then"] = None
            if then == "explore":
                d["state"] = "exploring"
                self.say(f"{d['name']} heads out into the wasteland.")

    # ---- items ----
    def storage_cap(self):
        mult = (10, 15, 20)
        return 10 + sum(mult[r["level"] - 1] * r["segs"] for r in self.rooms if r["type"] == "storage")

    def give_item(self, kind, name):
        if len(self.items) >= self.storage_cap():
            return False
        self.items.append({"id": self._id(), "kind": kind, "name": name})
        return True

    def item_value(self, it):
        if it["kind"] == "weapon":
            w = WEAPON[it["name"]]
            return 5 * (w[1] + w[2]) + 60 * w[3]
        o = OUTFIT[it["name"]]
        return 15 * sum(o[1].values()) + 60 * o[2]

    def random_item(self, luck=0, depth=0.0):
        x = self.rng.random() - luck * 0.01 - depth
        rarity = 2 if x < 0.03 else 1 if x < 0.2 else 0
        if self.rng.random() < 0.6:
            name = self.rng.choice([w[0] for w in WEAPONS if w[3] == rarity])
            return "weapon", name
        return "outfit", self.rng.choice([o[0] for o in OUTFITS if o[2] == rarity])

    def equip(self, d, item):
        """Swap an item from storage onto a dweller (whatever they had goes back into storage)."""
        if item not in self.items:
            return "That's gone"
        slot = "weapon" if item["kind"] == "weapon" else "outfit"
        self.items.remove(item)
        if d[slot]:
            self.items.append({"id": self._id(), "kind": item["kind"], "name": d[slot]})
        d[slot] = item["name"]
        d["hp"] = min(d["hp"], self.hp_cap(d))
        self.count("equips")
        return None

    def unequip(self, d, slot):
        if not d[slot]:
            return None
        if len(self.items) >= self.storage_cap():
            return "Storage is full"
        self.items.append({"id": self._id(), "kind": slot, "name": d[slot]})
        d[slot] = None
        return None

    def sell(self, item):
        if item in self.items:
            self.items.remove(item)
            v = self.item_value(item)
            self.caps += v
            return v
        return 0

    def damage(self, d):
        if d["weapon"]:
            w = WEAPON[d["weapon"]]
            avg = (w[1] + w[2]) / 2
        else:
            avg = 1.0
        return avg * (1 + d["level"] * 0.03) * 0.8

    # ---- resources ----
    def res_cap(self, key):
        makers = (key, "nuka") if key in ("food", "water") else (key,)
        segs = sum(r["segs"] * LEVEL_MULT[r["level"] - 1] for r in self.rooms
                   if ROOMS[r["type"]].get("produce") in makers)
        return 50 + 50 * segs

    def item_cap(self, key):
        kind = "medbay" if key == "stimpak" else "science"
        return 5 + sum(5 * r["segs"] * r["level"] for r in self.rooms if r["type"] == kind)

    def powered(self, room):
        return room["type"] in ("power", "door", "elevator") or self.res["power"] > 0

    def cycle(self, room):
        """Seconds for one production cycle, from the workers' stat (None if nobody's there)."""
        info = ROOMS[room["type"]]
        ds = self.present(room)
        if not ds:
            return None
        stat = sum(self.stat(d, info["stat"]) for d in ds)
        happy = sum(d["happy"] for d in ds) / len(ds)
        base = {"stimpak": 120, "radaway": 120, "nuka": 60}.get(info["produce"], 45)
        return base * 20 / (20 + stat * (0.5 + happy / 200))

    def amount(self, room):
        p = ROOMS[room["type"]]["produce"]
        if p in ("stimpak", "radaway"):
            return room["segs"] * room["level"]
        if p == "nuka":
            return 6 * room["segs"] * LEVEL_MULT[room["level"] - 1]
        return 8 * room["segs"] * LEVEL_MULT[room["level"] - 1]

    def collect(self, kind):
        """Collect every room that has this resource ready. (amount collected, caps found)"""
        got, caps = 0.0, 0
        for r in self.rooms:
            p = ROOMS[r["type"]].get("produce")
            if not r["ready"] or not (p == kind or (p == "nuka" and kind in ("food", "water"))):
                continue
            amt = r["ready"]
            if p == "nuka":
                for k in ("food", "water"):
                    self.res[k] = min(self.res_cap(k), self.res[k] + amt)
                self.count("food", amt)
                self.count("water", amt)
            elif p == "stimpak":
                self.stimpaks = min(self.item_cap("stimpak"), self.stimpaks + int(amt))
                self.count("stimpak", int(amt))
            elif p == "radaway":
                self.radaway = min(self.item_cap("radaway"), self.radaway + int(amt))
            else:
                self.res[p] = min(self.res_cap(p), self.res[p] + amt)
                self.count(p, amt)
            got += amt
            c = self.rng.randint(1, 4) * r["segs"] * r["level"]
            caps += c
            r["ready"] = 0.0
            r["prog"] = 0.0
            for d in self.present(r):
                self.gain_xp(d, 12)
                d["happy"] = min(100.0, d["happy"] + 2)
        self.caps += caps
        self.count("caps", caps)
        return got, caps

    def rush_risk(self, room):
        ds = self.present(room)
        luck = sum(self.stat(d, 6) for d in ds) / max(1, len(ds))
        return max(0.05, min(0.9, 0.3 + room["heat"] * 0.12 - luck * 0.02))

    def rush(self, room):
        if ROOMS[room["type"]]["kind"] != "produce" or room["ready"] or room["inc"] or not self.present(room):
            return "Nothing to rush"
        risk = self.rush_risk(room)
        room["heat"] += 1
        if self.rng.random() < risk:
            self.start_incident(room, self.rng.choice(["fire", "roaches"]))
            return "The rush failed!"
        room["ready"] = self.amount(room)
        room["prog"] = 1.0
        bonus = 10 * room["segs"] * room["level"]
        self.caps += bonus
        self.count("caps", bonus)
        self.count("rush_ok")
        for d in self.present(room):
            d["happy"] = min(100.0, d["happy"] + 10)
            self.gain_xp(d, 20)
        return None

    def gain_xp(self, d, n):
        if d["level"] >= 50:
            return
        d["xp"] += n
        while d["level"] < 50 and d["xp"] >= xp_needed(d["level"]):
            d["xp"] -= xp_needed(d["level"])
            before = self.max_hp(d)
            d["level"] += 1
            d["hp"] += self.max_hp(d) - before
            self.count("levelups")
            if d["state"] not in ("exploring", "returning"):
                self.say(f"{d['name']} reached level {d['level']}!", "level")

    # ---- incidents ----
    def door_max(self):
        return (100, 250, 500)[self.door()["level"] - 1]

    def start_incident(self, room, kind):
        info = INCIDENTS[kind]
        hp = info["hp"] * (room["segs"] if room["type"] != "door" else 1.5) * (1 + room["floor"] * 0.04)
        room["inc"] = {"kind": kind, "hp": hp, "max": hp, "t": 0.0, "idle": 0.0}
        where = ROOMS[room["type"]]["name"]
        if kind in ("raiders", "deathclaws"):
            self.say(f"{info['name']} are attacking the vault door!", "alert")
        else:
            self.say(f"{info['name']} in the {where}!", "alert")

    def _fighters(self, room):
        return [d for d in self.dwellers if self.located(d) is room and d["state"] == "idle" and self.adult(d)
                and d["preg"] <= 0]

    def _incident(self, room, dt):
        inc = room["inc"]
        info = INCIDENTS[inc["kind"]]
        fighters = self._fighters(room)
        inc["t"] += dt
        if room["type"] == "door" and info.get("moves") and self.door_hp > 0:
            self.door_hp = max(0.0, self.door_hp - 12 * dt)
            for d in fighters:
                inc["hp"] -= self.damage(d) * dt
        else:
            if not fighters and info.get("spread"):         # (left alone, it burns out or wanders off)
                inc["hp"] -= inc["max"] * 0.015 * dt
                inc["out"] = True
            for d in fighters:
                inc["hp"] -= self.damage(d) * dt
                inc["out"] = False
                d["fight"] = 1.0
                hurt = info["dmg"] * dt * (0.5 + 0.5 * inc["hp"] / inc["max"]) * (1 - 0.03 * self.stat(d, 2))
                hurt *= 1 + room["floor"] * 0.02
                d["hp"] -= max(0.0, hurt)
                if d["hp"] <= 0:
                    self.kill(d, f"was killed by {info['name'].lower()}")
        if inc["hp"] <= 0 and inc.get("out"):
            room["inc"] = None
            gone = "burned itself out" if inc["kind"] == "fire" else "wandered off"
            self.say(f"The {info['name'].lower()} in the {ROOMS[room['type']]['name']} {gone}.", "info")
            return
        if inc["hp"] <= 0:
            room["inc"] = None
            caps = int(info["caps"] * (1 + room["floor"] * 0.05))
            self.caps += caps
            self.count("caps", caps)
            self.count("incidents")
            if inc["kind"] == "fire":
                self.count("fires")
            for d in fighters:
                self.gain_xp(d, inc["max"] / 4)
                d["happy"] = min(100.0, d["happy"] + 5)
            self.say(f"The {info['name'].lower()} in the {ROOMS[room['type']]['name']} are dealt with. +{caps} caps",
                     "good")
            return
        inc["idle"] = 0.0 if fighters else inc["idle"] + dt
        burning = sum(1 for r in self.rooms if r["inc"])
        if info.get("spread") and inc["t"] > 30 and not inc.get("spread") and burning < 4:
            inc["spread"] = True
            nb = [r for r in self.adjacent(room) if not r["inc"] and r["type"] not in ("elevator", "door")]
            if nb:
                other = self.rng.choice(nb)
                self.start_incident(other, inc["kind"])
                other["inc"]["hp"] = other["inc"]["max"] * 0.6
                other["inc"]["spread"] = True
        if info.get("moves") and (inc["idle"] > 12 or inc["t"] > 45):
            nb = [r for r in self.adjacent(room) if not r["inc"] and r["type"] != "elevator"]
            nb.sort(key=lambda r: (r["floor"], r["cell"]))
            if nb:
                nxt = nb[-1] if self.rng.random() < 0.6 else self.rng.choice(nb)
                nxt["inc"] = dict(inc, t=0.0, idle=0.0)
                room["inc"] = None
                stolen = int(self.caps * 0.04)
                self.caps -= stolen
                self.say(f"{info['name']} push into the {ROOMS[nxt['type']]['name']}" +
                         (f" and steal {stolen} caps!" if stolen else "!"), "alert")
            elif inc["t"] > 90:
                room["inc"] = None
                self.say(f"The {info['name'].lower()} leave the vault.", "info")

    def adjacent(self, room):
        """Rooms beside this one - straight next door, or across an elevator shaft one floor up, down or level."""
        out = {}
        f, c0, w = room["floor"], room["cell"], width(room)
        for c in (c0 - 1, c0 + w):
            r = self.room_at(f, c)
            if r is None:
                continue
            if r["type"] != "elevator":
                out[r["id"]] = r
                continue
            for df in (-1, 0, 1):
                e = self.room_at(f + df, c)
                if e is None or e["type"] != "elevator":
                    continue
                for cc in (c - 1, c + 1):
                    o = self.room_at(f + df, cc)
                    if o and o is not room and o["type"] != "elevator":
                        out[o["id"]] = o
        return list(out.values())

    def kill(self, d, how):
        d["state"] = "dead" if d["state"] not in ("exploring", "returning") else "dead_out"
        d["hp"] = 0.0
        d["path"] = []
        if d["preg"] > 0:
            d["preg"] = 0.0
        self.say(f"{d['name']} {how}.", "death")

    def revive_cost(self, d):
        return 100 + 25 * d["level"]

    def revive(self, d):
        cost = self.revive_cost(d)
        if self.caps < cost:
            return "Not enough caps"
        self.caps -= cost
        d["hp"] = self.hp_cap(d)
        if d["state"] == "dead_out":
            d["state"] = "returning"
            d["ex"]["ret"] = max(30.0, d["ex"]["t"] / 2)
            d["ex"]["log"].append("Revived - heading home.")
        else:
            d["state"] = "idle"
        self.say(f"{d['name']} is back on their feet.", "good")
        return None

    def bury(self, d):
        if d["state"] in ("dead", "dead_out"):
            self.dwellers.remove(d)

    def heal(self, d):
        if self.stimpaks <= 0:
            return "No Stimpaks"
        if d["hp"] >= self.hp_cap(d):
            return "They're fine"
        self.stimpaks -= 1
        d["hp"] = min(self.hp_cap(d), d["hp"] + self.max_hp(d) * 0.4)
        return None

    def cure(self, d):
        if self.radaway <= 0:
            return "No RadAway"
        if d["rad"] <= 0:
            return "They're not irradiated"
        self.radaway -= 1
        d["rad"] = max(0.0, d["rad"] - self.max_hp(d) * 0.3)
        return None

    # ---- the wasteland ----
    def explore(self, d, stims, rads):
        if not self.adult(d) or d["preg"] > 0 or d["state"] not in ("idle", "walking"):
            return "They can't go out now"
        stims, rads = min(stims, self.stimpaks), min(rads, self.radaway)
        self.stimpaks -= stims
        self.radaway -= rads
        d["stim"], d["radaway"] = stims, rads
        d["room"] = None
        d["ex"] = {"t": 0.0, "next": 20.0, "caps": 0, "items": [], "log": ["Left the vault."], "ret": 0.0}
        self.walk_to(d, self.door(), then="explore")
        return None

    def recall(self, d):
        if d["state"] != "exploring":
            return "They're not out exploring"
        d["state"] = "returning"
        d["ex"]["ret"] = max(10.0, d["ex"]["t"] / 2)
        d["ex"]["log"].append("Heading home.")
        return None

    def _wasteland(self, d, dt):
        ex = d["ex"]
        if d["state"] == "returning":
            ex["ret"] -= dt
            if ex["ret"] <= 0:
                self._home(d)
            return
        ex["t"] += dt
        if int(ex["t"] / 60) > int((ex["t"] - dt) / 60):
            self.count("explore_min")
        d["rad"] = min(self.max_hp(d) * 0.9, d["rad"] + 0.012 * dt)
        ex["next"] -= dt
        if ex["next"] > 0:
            return
        rng = self.rng
        ex["next"] = rng.uniform(18, 35)
        depth = min(0.15, ex["t"] / 6000)
        x = rng.random()
        mins = int(ex["t"] // 60)
        stamp = f"{mins}m"
        if x < 0.3:
            c = rng.randint(3, 12) + int(ex["t"] / 60) + self.stat(d, 6)
            ex["caps"] += c
            ex["log"].append(f"{stamp}: Found {c} caps at {rng.choice(PLACES)}.")
        elif x < 0.42:
            kind, name = self.random_item(self.stat(d, 6), depth)
            ex["items"].append([kind, name])
            ex["log"].append(f"{stamp}: Found a {name} in {rng.choice(PLACES)}!")
        elif x < 0.72:
            pool = CREATURES[:2 + min(len(CREATURES) - 2, int(ex["t"] / 240))]
            foe, power = rng.choice(pool)
            hurt = power * rng.uniform(0.6, 1.4) * (1 - 0.03 * self.stat(d, 2)) / (1 + self.damage(d) / 10)
            d["hp"] -= hurt
            self.gain_xp(d, power * 3)
            ex["log"].append(f"{stamp}: Fought off {foe} (-{int(hurt)} HP).")
            if rng.random() < 0.3:
                c = rng.randint(5, 20)
                ex["caps"] += c
                ex["log"].append(f"{stamp}: It had {c} caps.")
        else:
            ex["log"].append(f"{stamp}: Passed {rng.choice(PLACES)}. Nothing worth taking.")
        if d["hp"] < self.hp_cap(d) * 0.35 and d["stim"] > 0:
            d["stim"] -= 1
            d["hp"] = min(self.hp_cap(d), d["hp"] + self.max_hp(d) * 0.4)
            ex["log"].append(f"{stamp}: Used a Stimpak.")
        if d["rad"] > self.max_hp(d) * 0.3 and d["radaway"] > 0:
            d["radaway"] -= 1
            d["rad"] = max(0.0, d["rad"] - self.max_hp(d) * 0.3)
            ex["log"].append(f"{stamp}: Used a RadAway.")
        if d["hp"] <= 0:
            ex["log"].append(f"{stamp}: Didn't make it.")
            self.kill(d, "died out in the wasteland")
        del ex["log"][:-40]

    def _home(self, d):
        ex = d["ex"]
        self.caps += ex["caps"]
        self.count("caps", ex["caps"])
        kept = sum(1 for kind, name in ex["items"] if self.give_item(kind, name))
        lost = len(ex["items"]) - kept
        self.stimpaks += d["stim"]
        self.radaway += d["radaway"]
        d["stim"] = d["radaway"] = 0
        door = self.door()
        d["state"] = "idle"
        d["x"], d["y"] = door["cell"] + 1.0, float(door["floor"])
        d["room"] = None
        self.say(f"{d['name']} is home with {ex['caps']} caps and {len(ex['items'])} item"
                 f"{'' if len(ex['items']) == 1 else 's'}" + (f" ({lost} left behind: storage is full)" if lost else "")
                 + ".", "good")
        d["ex"] = None

    # ---- objectives and lunchboxes ----
    def _new_objective(self):
        taken = {o["key"] for o in self.objectives}
        pool = [o for o in OBJECTIVES if o[1] not in taken]
        text, key, steps = self.rng.choice(pool)
        done = self.counters.get(f"obj_{key}", 0)
        n = steps[min(len(steps) - 1, done)]
        reward = ["lunchbox", 1] if self.rng.random() < 0.3 else ["caps", 50 * (1 + min(2, done)) + 50]
        self.objectives.append({"text": text.format(n=n), "key": key, "target": n,
                                "start": self.counters.get(key, 0), "reward": reward})

    def progress(self, o):
        return min(o["target"], int(self.counters.get(o["key"], 0) - o["start"]))

    def claim(self, o):
        if self.progress(o) < o["target"]:
            return "Not finished yet"
        self.objectives.remove(o)
        self.count(f"obj_{o['key']}")
        kind, n = o["reward"]
        if kind == "caps":
            self.caps += n
        else:
            self.lunchboxes += n
        self._new_objective()
        return None

    def open_lunchbox(self):
        """Four cards (at least one rare or better). Returns them; they're already yours."""
        if self.lunchboxes <= 0:
            return []
        self.lunchboxes -= 1
        cards = []
        for i in range(4):
            x = self.rng.random()
            if i == 3 and not any(c["rarity"] for c in cards):
                x = min(x, 0.25)
            if x < 0.03 and self.population() < max(self.capacity(), 1):
                name, sex, special = self.rng.choice(LEGENDS)
                if not any(d["name"] == name for d in self.dwellers):
                    self.new_dweller(sex=sex, special=special, name=name, legendary=True)
                    self.count("arrivals")
                    cards.append({"kind": "dweller", "label": name, "rarity": 2})
                    continue
            if x < 0.1:
                kind, name = self.random_item(depth=0.15)
                if self.give_item(kind, name):
                    cards.append({"kind": kind, "label": name,
                                  "rarity": (WEAPON[name][3] if kind == "weapon" else OUTFIT[name][2])})
                    continue
            if x < 0.25:
                n = self.rng.choice([3, 4, 5])
                if self.rng.random() < 0.5:
                    self.stimpaks += n
                    cards.append({"kind": "stimpak", "label": f"{n} Stimpaks", "rarity": 1})
                else:
                    self.radaway += n
                    cards.append({"kind": "radaway", "label": f"{n} RadAway", "rarity": 1})
                continue
            if x < 0.6:
                k = self.rng.choice(["power", "food", "water"])
                n = self.rng.choice([50, 100, 150])
                self.res[k] = min(self.res_cap(k), self.res[k] + n)
                cards.append({"kind": k, "label": f"{n} {RESOURCES[k][1]}", "rarity": 0})
                continue
            n = self.rng.choice([50, 100, 100, 250, 500])
            self.caps += n
            cards.append({"kind": "caps", "label": f"{n} Caps", "rarity": 1 if n >= 250 else 0})
        return cards

    # ---- the clock ----
    def update(self, dt, offline=False):
        self.time += dt
        alive = [d for d in self.dwellers if d["state"] not in ("dead", "dead_out")]
        home = [d for d in alive if d["state"] not in ("exploring", "returning")]
        if not offline:
            eat = sum(0.5 if d["child"] > 0 else 1.0 for d in home) * 0.36 / 60 * dt
            self.res["food"] = max(0.0, self.res["food"] - eat)
            self.res["water"] = max(0.0, self.res["water"] - eat)
            draw = sum(r["segs"] for r in self.rooms if r["type"] not in ("door", "elevator", "power"))
            self.res["power"] = max(0.0, self.res["power"] - draw * 0.6 / 60 * dt)
        powered = self.res["power"] > 0
        for k in ("power", "food", "water"):
            self.res[k] = min(self.res[k], self.res_cap(k))
        # the rooms
        for r in self.rooms:
            info = ROOMS[r["type"]]
            r["heat"] = max(0.0, r["heat"] - dt / 120)
            if r["inc"]:
                if not offline:
                    self._incident(r, dt)
                continue
            if not (powered or r["type"] == "power"):
                continue
            kind = info["kind"]
            if kind == "produce" and not r["ready"]:
                c = self.cycle(r)
                if c:
                    r["prog"] += dt / c
                    if r["prog"] >= 1:
                        r["prog"] = 1.0
                        r["ready"] = self.amount(r)
            elif kind == "training":
                st = info["stat"]
                for d in self.present(r):
                    if d["special"][st] >= 10:
                        continue
                    need = 25 * d["special"][st] / (1 + 0.25 * (r["level"] - 1))
                    d["train"] += dt
                    if d["train"] >= need:
                        d["train"] = 0.0
                        d["special"][st] += 1
                        self.count("trained")
                        self.gain_xp(d, 10)
                        self.say(f"{d['name']}'s {STAT_NAMES[st]} is now {d['special'][st]}.", "level")
            elif kind == "radio":
                pull = sum(self.stat(d, 3) for d in self.present(r)) * LEVEL_MULT[r["level"] - 1]
                self.radio += dt * pull / 900
            elif kind == "living":
                self._romance(r, dt)
        if self.radio >= 1 and len(alive) + self._babies() < self.capacity():
            self.radio = 0.0
            self._arrive("The radio brought in a new dweller")
        self.radio = min(self.radio, 1.0)
        # the dwellers
        for d in self.dwellers:
            st = d["state"]
            if st in ("dead", "dead_out"):
                continue
            if st in ("exploring", "returning"):
                self._wasteland(d, dt)
                continue
            if d["child"] > 0:
                d["child"] -= dt
                if d["child"] <= 0:
                    self.say(f"{d['name']} has grown up and is ready to work.", "good")
            if d["preg"] > 0:
                d["preg"] -= dt
                if d["preg"] <= 0:
                    self._birth(d)
            d["cool"] = max(0.0, d["cool"] - dt)
            d["fight"] = max(0.0, d["fight"] - dt)
            if st == "walking":
                self._move(d, dt)
            elif not offline:
                self._wander(d, dt)
            # health and radiation
            if self.res["food"] <= 0:
                d["hp"] -= 0.04 * dt
            elif d["hp"] < self.hp_cap(d) and not d["fight"]:
                d["hp"] = min(self.hp_cap(d), d["hp"] + 0.05 * dt)
            if self.res["water"] <= 0:
                d["rad"] = min(self.max_hp(d) * 0.9, d["rad"] + 0.04 * dt)
            d["hp"] = min(d["hp"], self.hp_cap(d))
            if d["hp"] <= 0:
                self.kill(d, "starved" if self.res["food"] <= 0 else "died")
                continue
            # happiness drifts toward how things are
            room = self.room(d["room"]) if d["room"] else None
            target = 45.0
            if d["child"] > 0:
                target = 75.0
            elif room:
                target = 70.0 if self.ideal(d, room) else 52.0
            for k in ("power", "food", "water"):
                if self.res[k] <= 0:
                    target -= 18
            target += min(10.0, sum(r["level"] * r["segs"] * 2 for r in self.rooms if r["type"] == "radio"))
            if d["hp"] < self.hp_cap(d) * 0.5:
                target -= 10
            target = max(10.0, min(100.0, target))
            d["happy"] += (target - d["happy"]) * min(1.0, dt / 90)
        if not offline:
            self._random_events(dt, len(alive))

    def _wander(self, d, dt):
        here = self.located(d)
        if here is None or here["type"] == "elevator":
            return
        d["wander"] -= dt
        if d["wx"] is not None:
            dx = d["wx"] - d["x"]
            step = 0.6 * dt
            if abs(dx) <= step:
                d["x"] = d["wx"]
                d["wx"] = None
            else:
                d["x"] += step if dx > 0 else -step
                d["face"] = 1 if dx > 0 else -1
        elif d["wander"] <= 0:
            d["wander"] = self.rng.uniform(3, 9)
            if self.rng.random() < 0.6 and not here["inc"]:
                d["wx"] = here["cell"] + 0.4 + self.rng.random() * (width(here) - 0.8)

    def _babies(self):
        return sum(1 for d in self.dwellers if d["preg"] > 0)

    def _related(self, a, b):
        return (a["id"] in b["parents"] or b["id"] in a["parents"]
                or bool(set(a["parents"]) & set(b["parents"])))

    def _romance(self, r, dt):
        ds = [d for d in self.present(r) if d["preg"] <= 0 and d["cool"] <= 0]
        men = [d for d in ds if d["sex"] == "M"]
        women = [d for d in ds if d["sex"] == "F"]
        pair = next(((m, w) for m in men for w in women if not self._related(m, w)), None)
        pop = self.population() + self._babies()
        if pair is None or pop >= self.capacity():
            r["rom"] = 0.0
            return
        r["rom"] += dt * (1 + 0.05 * (self.stat(pair[0], 3) + self.stat(pair[1], 3)))
        if r["rom"] >= 40:
            r["rom"] = 0.0
            m, w = pair
            w["preg"] = 180.0
            w["partner"] = m["id"]
            m["cool"] = w["cool"] = 120.0
            m["happy"] = w["happy"] = 100.0
            self.say(f"{w['name']} and {m['name']} are expecting a baby!", "good")

    def _birth(self, mother):
        father = self.dweller(mother.get("partner"))
        parents = [mother["id"]] + ([father["id"]] if father else [])
        surname = mother["name"].split()[-1]
        sex = self.rng.choice("MF")
        first = self.rng.choice(FIRST_M if sex == "M" else FIRST_F)
        special = [max(1, min(10, (mother["special"][i] + (father["special"][i] if father else 2)) // 2
                              + self.rng.randint(-1, 1))) for i in range(7)]
        kid = self.new_dweller(at_door=False, sex=sex, special=special, name=f"{first} {surname}", child=180.0,
                               parents=parents)
        kid["x"], kid["y"] = mother["x"], mother["y"]
        kid["room"] = mother["room"] if mother["room"] and self.room(mother["room"])["type"] == "living" else None
        self.count("births")
        self.say(f"{kid['name']} was born!", "good")

    def _arrive(self, why):
        d = self.new_dweller(at_door=True)
        self.count("arrivals")
        self.say(f"{why}: {d['name']} is at the door.", "good")
        return d

    def _random_events(self, dt, pop):
        self.next_arrival -= dt
        if self.next_arrival <= 0:
            self.next_arrival = self.rng.uniform(200, 420)
            if pop < self.capacity() and pop < 30:
                self._arrive("A wanderer found the vault")
        self.next_incident -= dt
        if self.next_incident <= 0:
            self.next_incident = self.rng.uniform(240, 480)
            if pop < 8 or any(r["inc"] for r in self.rooms):
                return
            kinds = [k for k, v in INCIDENTS.items() if v["pop"] <= pop]
            kind = self.rng.choice(kinds)
            if INCIDENTS[kind].get("moves"):
                self.door_hp = self.door_max()
                self.start_incident(self.door(), kind)
            else:
                rooms = [r for r in self.rooms if r["type"] not in ("elevator", "door")]
                busy = [r for r in rooms if self.present(r)]
                self.start_incident(self.rng.choice(busy or rooms), kind)

    # ---- summary ----
    def happiness(self):
        ds = [d for d in self.dwellers if d["state"] not in ("dead", "dead_out", "exploring", "returning")]
        return sum(d["happy"] for d in ds) / len(ds) if ds else 0.0
