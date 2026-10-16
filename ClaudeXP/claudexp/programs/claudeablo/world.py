"""Claudeablo's rules: the hero, monsters, combat, spells, loot, shrines, portals and the trip down to Diablo.

Everything here is in tile units (a tile is 1.0 wide) and seconds. The screen calls World.update(dt) every frame
and the command methods (move_to, attack, interact, cast, use_belt, ...) when you click and press keys.
"""
import math
import random

from . import dungeon as D
from . import items as I

CLASSES = {
    # base stats, life per vitality / per level, mana per magic / per level, block %, move speed, attack time
    "warrior": dict(str=30, dex=20, mag=10, vit=25, lpv=2.0, lpl=2.0, mpm=1.0, mpl=1.0, block=30, speed=4.0,
                    swing=0.95, start=["Short Sword", "Buckler", "Quilted Armor"], spells=[]),
    "rogue": dict(str=20, dex=30, mag=15, vit=20, lpv=1.5, lpl=1.5, mpm=1.25, mpl=1.5, block=20, speed=4.3,
                  swing=0.85, start=["Short Bow", "Quilted Armor"], spells=[]),
    "sorcerer": dict(str=15, dex=15, mag=35, vit=20, lpv=1.0, lpl=1.0, mpm=2.0, mpl=2.0, block=10, speed=4.0,
                     swing=1.0, start=["Short Staff", "Rags"], spells=["Firebolt"]),
}
FACINGS = {(1, 0): 0, (0, 1): 1, (-1, 0): 3, (0, -1): 2}     # 0 SE  1 SW  2 NE  3 NW  (screen directions)

MONSTERS = {
    # kind: (name, look, hp, (dmg lo, hi), ac, speed tiles/s, xp, ai, missile)
    "zombie": ("Zombie", "zombie", 16, (2, 5), 5, 1.1, 20, "melee", None),
    "ghoul": ("Ghoul", "ghoul", 30, (4, 9), 12, 1.4, 45, "melee", None),
    "skeleton": ("Skeleton", "skeleton", 11, (1, 5), 10, 2.0, 22, "melee", None),
    "skeleton_archer": ("Skeleton Archer", "skeleton_archer", 9, (1, 4), 8, 1.8, 26, "ranged", "arrow"),
    "fallen": ("Fallen One", "fallen", 8, (1, 4), 8, 2.6, 15, "pack", None),
    "scavenger": ("Scavenger", "beast", 10, (1, 5), 6, 3.0, 18, "melee", None),
    "bat": ("Fiend", "bat", 7, (1, 4), 12, 3.2, 20, "erratic", None),
    "goatman": ("Goatman", "goatman", 24, (3, 8), 15, 2.2, 48, "melee", None),
    "hidden": ("Hidden", "hidden", 22, (3, 9), 20, 2.6, 60, "stealth", None),
    "hellwitch": ("Hell Witch", "hellwitch", 26, (2, 6), 18, 2.0, 80, "caster", "firebolt"),
    "knight": ("Black Knight", "knight", 62, (8, 16), 40, 1.9, 140, "melee", None),
    "magma": ("Magma Demon", "magma", 56, (6, 14), 30, 1.6, 150, "caster", "fireball"),
    "pitlord": ("Pit Lord", "pitlord", 120, (12, 26), 45, 1.8, 300, "melee", None),
    "diablo": ("Diablo", "diablo", 260, (20, 40), 60, 2.0, 5000, "diablo", "redbolt"),
}
THEME_MONSTERS = {
    "cathedral": ["zombie", "zombie", "skeleton", "skeleton", "skeleton_archer", "fallen", "fallen", "scavenger",
                  "bat"],
    "catacombs": ["skeleton", "skeleton_archer", "ghoul", "goatman", "goatman", "bat", "hidden", "fallen"],
    "caves": ["goatman", "scavenger", "hidden", "magma", "bat", "ghoul"],
    "hell": ["hellwitch", "knight", "magma", "goatman", "hidden", "hellwitch"],
    "abyss": ["knight", "pitlord", "hellwitch", "magma", "knight"],
}
BOSSES = {
    5: ("The Butcher", "ghoul", dict(skin="#B04040", body="#5A1A1A", size=1.45, weapon="axe")),
    15: ("The Bone King", "skeleton", dict(size=1.5, head="skull", skin="#F0E4B0")),
    25: ("Ignis the Lavalord", "magma", dict(size=1.7)),
    35: ("Azmorath the Black", "knight", dict(size=1.5, body="#14141A", trim="#E02020")),
    45: ("Baalzeth the Pit Lord", "pitlord", dict(size=1.8)),
}
CHAMP_A = ["Bloodlust", "Gorefeast", "Blightfang", "Rotclaw", "Soulripper", "Grimjaw", "Ashbringer", "Doomhowl",
           "Bonegnaw", "Vilespawn", "Deathwhisper", "Hollowgaze"]
CHAMP_B = ["the Cursed", "the Unclean", "the Cold", "the Hungry", "the Wretched", "the Defiler", "the Fiery",
           "the Vile", "the Mad", "the Ancient"]
SHRINES = [("Glimmering Shrine", "#F8F0A0"), ("Divine Shrine", "#FFFFFF"), ("Eerie Shrine", "#A060FF"),
           ("Abandoned Shrine", "#60FF90"), ("Creepy Shrine", "#FF6060"), ("Quiet Shrine", "#FFA040"),
           ("Hidden Shrine", "#60C0FF"), ("Ornate Shrine", "#FF40C0"), ("Gloomy Shrine", "#8080A0"),
           ("Fascinating Shrine", "#40E0E0")]


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def facing_for(dx, dy):
    """Screen-direction facing from a movement in tile space (x runs down-right, y down-left on screen)."""
    sx, sy = dx - dy, dx + dy                 # screen-ish direction
    if abs(sx) < 1e-6 and abs(sy) < 1e-6:
        return None
    if sy >= 0:
        return 0 if sx >= 0 else 1
    return 2 if sx >= 0 else 3


class Actor:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.facing = 0
        self.pose = "stand"
        self.phase = random.random() * 6
        self.anim = 0.0                       # time left in an attack / cast / hit animation
        self.hurt = 0.0
        self.dead = False
        self.path = []

    def tile(self):
        return (int(self.x), int(self.y))


class Player(Actor):
    def __init__(self, cls="warrior", name="Hero"):
        super().__init__(0, 0)
        c = CLASSES[cls]
        self.cls, self.name = cls, name
        self.level, self.xp, self.points = 1, 0, 0
        self.base = {k: c[k] for k in ("str", "dex", "mag", "vit")}
        self.gold = 100
        self.inv = [None] * 40
        self.equip = {k: None for k in ("weapon", "shield", "helm", "armor", "amulet", "ring1", "ring2")}
        self.belt = [None] * 4
        self.spells = {s: 1 for s in c["spells"]}
        self.active_spell = c["spells"][0] if c["spells"] else None
        self.max_depth = 0
        self.buffs = {}                        # name -> seconds left
        self.target = None
        self.cool = 0.0
        self.repath_t = 0.0
        self.hit_pending = None
        for base in c["start"]:
            it = I.make(base, 1)
            self.equip[I.slot(it)] = it
        for _ in range(2):
            self.belt_add(I.make("Potion of Healing"))
        if cls == "sorcerer":
            self.belt_add(I.make("Potion of Mana"))
        self.add_item(I.make("Scroll of Town Portal"))
        self.recalc()
        self.hp, self.mana = self.maxhp, self.maxmana

    # ---- stats -------------------------------------------------------------------------------------------
    def items(self):
        return [it for it in self.equip.values() if it]

    def affix(self, name):
        return sum(I.stat(it, name) for it in self.items())

    def recalc(self):
        c = CLASSES[self.cls]
        self.str_ = self.base["str"] + self.affix("str")
        self.dex = self.base["dex"] + self.affix("dex")
        self.mag = self.base["mag"] + self.affix("mag")
        self.vit = self.base["vit"] + self.affix("vit")
        self.maxhp = int(20 + self.vit * c["lpv"] + self.level * c["lpl"] + self.affix("life"))
        staff = 20 if self.equip["weapon"] and I.kind(self.equip["weapon"]) == "staff" else 0
        self.maxmana = int(self.mag * c["mpm"] + self.level * c["mpl"] + self.affix("mana") + staff)
        self.ac = sum(I.armour(it) for it in self.items() if I.slot(it) in ("armor", "helm", "shield")) + \
            self.dex // 5
        if self.buffs.get("Hidden Shrine"):
            self.ac = int(self.ac * 1.5)
        self.to_hit = 50 + self.dex // 2 + self.level + self.affix("to_hit")
        w = self.equip["weapon"]
        self.ranged = bool(w and I.kind(w) == "bow")
        lo, hi = I.damage(w) if w else (1, 3)
        mult = 1 + self.affix("dmg_pct") / 100 + (0.3 if self.buffs.get("Gloomy Shrine") else 0)
        flat = (self.dex if self.ranged else self.str_) / 8 + self.level * 0.2
        self.dmg = (max(1, int(lo * mult + flat)), max(2, int(hi * mult + flat)))
        self.elem = self.affix("fire_dmg") + self.affix("light_dmg")
        self.swing = c["swing"] * (1 - min(0.5, self.affix("speed") / 100))
        self.block = min(75, c["block"] + self.dex // 4) if self.equip["shield"] else 0
        self.res_fire = min(75, self.affix("res_fire"))
        self.res_light = min(75, self.affix("res_light"))
        self.leech = self.affix("leech")
        self.thorns = self.affix("thorns")
        self.regen = self.affix("regen")
        self.light = 7 + self.affix("light_radius")
        self.spell_bonus = self.affix("spell_lvl")
        self.speed = c["speed"]
        if hasattr(self, "hp"):
            self.hp = min(self.hp, self.maxhp)
            self.mana = min(self.mana, self.maxmana)

    def can_equip(self, item):
        s, d, m = I.requirements(item)
        return self.str_ >= s and self.dex >= d and self.mag >= m

    def next_level_xp(self):
        return int(40 * self.level ** 1.75 + 40)

    # ---- the pack and belt -------------------------------------------------------------------------------
    def add_item(self, item):
        if item["rarity"] == "supply":
            for i, it in enumerate(self.inv):          # potions and scrolls stack
                if it and it["base"] == item["base"] and I.kind(it) in ("potion", "scroll") and it["qty"] < 20:
                    it["qty"] += item.get("qty", 1)
                    return True
        for i, it in enumerate(self.inv):
            if it is None:
                self.inv[i] = item
                return True
        return False

    def belt_add(self, item):
        if I.kind(item) != "potion":
            return False
        for i, it in enumerate(self.belt):
            if it is None:
                self.belt[i] = item
                return True
        return False

    def count(self, base):
        return sum(it["qty"] for it in self.inv if it and it["base"] == base)

    def take_one(self, base):
        for i, it in enumerate(self.inv):
            if it and it["base"] == base:
                it["qty"] -= 1
                if it["qty"] <= 0:
                    self.inv[i] = None
                return True
        return False

    def to_json(self):
        return {"cls": self.cls, "name": self.name, "level": self.level, "xp": self.xp, "points": self.points,
                "base": self.base, "gold": self.gold, "inv": self.inv, "equip": self.equip, "belt": self.belt,
                "spells": self.spells, "active_spell": self.active_spell, "max_depth": self.max_depth,
                "hp": self.hp, "mana": self.mana}

    @classmethod
    def from_json(cls, d):
        p = cls(d["cls"], d["name"])
        for k in ("level", "xp", "points", "base", "gold", "inv", "equip", "belt", "spells", "active_spell",
                  "max_depth"):
            setattr(p, k, d[k])
        p.recalc()
        p.hp, p.mana = min(d.get("hp", p.maxhp), p.maxhp), min(d.get("mana", p.maxmana), p.maxmana)
        return p


class Monster(Actor):
    def __init__(self, x, y, kind, mlevel, rnd, champion=False, boss=None):
        super().__init__(x, y)
        name, look, hp, (lo, hi), ac, speed, xp, ai, missile = MONSTERS[kind]
        self.kind, self.look, self.ai, self.missile = kind, look, ai, missile
        self.mlevel = mlevel
        grow = 1 + 0.29 * (mlevel - 1)
        dmg_grow = 1 + 0.12 * (mlevel - 1)
        self.maxhp = hp * grow * rnd.uniform(0.85, 1.15)
        self.dmg = (lo * dmg_grow, hi * dmg_grow)
        self.ac = ac * (1 + 0.08 * (mlevel - 1))
        self.to_hit = 70 + 1.2 * mlevel
        self.speed = speed
        self.xp = xp * (1 + 0.15 * (mlevel - 1))
        self.name = name
        self.looks = {}
        self.champion = champion
        self.boss = boss is not None
        self.res = {"fire": 0, "light": 0}
        if kind in ("magma", "hellwitch", "diablo"):
            self.res["fire"] = 50
        if kind in ("skeleton", "skeleton_archer"):
            self.res["light"] = 25
        if champion:
            self.name = f"{rnd.choice(CHAMP_A)} {rnd.choice(CHAMP_B)}"
            self.maxhp *= 3
            self.dmg = (self.dmg[0] * 1.5, self.dmg[1] * 1.5)
            self.xp *= 3
            self.looks = {"size": 1.15}
        if boss:
            self.name, _look, self.looks = boss
            self.look = _look
            self.maxhp *= 7
            self.dmg = (self.dmg[0] * 1.8, self.dmg[1] * 1.8)
            self.xp *= 10
            self.ac *= 1.3
        if kind == "diablo":
            self.maxhp = 9000
            self.dmg = (60, 120)
            self.ac = 260
            self.to_hit = 150
            self.boss = True
        self.hp = self.maxhp
        self.state = "idle"
        self.home = (x, y)
        self.cool = rnd.uniform(0, 1.5)
        self.repath = 0.0
        self.special = 0.0
        self.flee = 0.0
        self.seen = False
        self.zig = rnd.uniform(0, 6)


class Missile:
    def __init__(self, kind, x, y, dx, dy, speed, dmg, owner, elem="phys", radius=0.35, life=2.5):
        n = math.hypot(dx, dy) or 1
        self.kind, self.x, self.y = kind, x, y
        self.vx, self.vy = dx / n * speed, dy / n * speed
        self.dmg, self.owner, self.elem, self.radius, self.life = dmg, owner, elem, radius, life
        self.hit = set()
        self.dead = False


class GroundItem:
    def __init__(self, x, y, item):
        self.x, self.y, self.item = x, y, item


class Obj:
    def __init__(self, kind, x, y, **kw):
        self.kind, self.x, self.y = kind, x, y
        self.opened = False
        self.__dict__.update(kw)


class NPC(Actor):
    def __init__(self, x, y, role, name, look):
        super().__init__(x, y)
        self.role, self.name, self.look = role, name, look
        self.home = (x, y)
        self.wait = random.uniform(1, 4)


# ---- the world --------------------------------------------------------------------------------------------------

class World:
    def __init__(self, seed, player):
        self.seed = seed
        self.player = player
        self.rnd = random.Random(seed)
        self.depth = 0
        self.level = None
        self.monsters, self.missiles, self.ground, self.objects, self.npcs = [], [], [], [], []
        self.effects = []                   # visual effects for the screen: dicts with a 'ttl'
        self.messages = []                  # (text, colour, time)
        self.portal = None                  # (depth, x, y) of an open town portal
        self.flags = {"diablo_dead": False}
        self.time = 0.0
        self.explored = set()
        self.dead = False
        self.won_at = None
        self.shop_stock = {}
        self.talk_to = None                 # the townsperson you just walked up to (the screen opens their shop)
        self.waystone_open = False
        self.enter(0)

    # ---- talking to the screen ---------------------------------------------------------------------------
    def say(self, text, colour="#E8E0C8"):
        self.messages.append((text, colour, self.time))
        del self.messages[:-8]

    def fx(self, kind, **kw):
        kw.setdefault("ttl", 0.5)
        kw["kind"] = kind
        kw["t0"] = self.time
        self.effects.append(kw)

    # ---- moving between places -------------------------------------------------------------------------
    def enter(self, depth, arrive="up"):
        self.depth = depth
        self.monsters, self.missiles, self.ground, self.objects, self.npcs = [], [], [], [], []
        self.effects = []
        self.explored = set()
        p = self.player
        p.path, p.target = [], None
        if depth == 0:
            self.level = D.town()
            lv = self.level
            spot = {"down": lv.down, "portal": lv.places["portal"], "waystone": lv.places["waystone"]}.get(
                arrive, lv.spawn)
            self._place(spot)
            self._town_people()
            self.objects.append(Obj("stairs_down", lv.down[0] + 0.5, lv.down[1] + 0.5))
            self.objects.append(Obj("waystone", lv.places["waystone"][0] + 0.5, lv.places["waystone"][1] + 0.5))
            if self.portal:
                px, py = lv.places["portal"]
                self.objects.append(Obj("portal", px + 0.5, py + 0.5))
            self._restock()
            if p.hp < p.maxhp * 0.3:
                self.say("You're badly hurt. Pepin the healer can help.", "#FFB080")
            self.explored = {(x, y) for y in range(lv.h) for x in range(lv.w)}
            return
        self.level = D.generate(self.seed, depth)
        lv = self.level
        p.max_depth = max(p.max_depth, depth)
        if lv.up:
            self.objects.append(Obj("stairs_up", lv.up[0] + 0.5, lv.up[1] + 0.5))
        if lv.down:
            self.objects.append(Obj("stairs_down", lv.down[0] + 0.5, lv.down[1] + 0.5))
        if arrive == "down" and lv.down:
            self._place(D._near_free(lv, lv.down))
        elif arrive == "portal" and self.portal and self.portal[0] == depth:
            self._place((int(self.portal[1]), int(self.portal[2])))
        else:
            self._place(lv.spawn)
        if self.portal and self.portal[0] == depth:
            self.objects.append(Obj("portal", self.portal[1], self.portal[2]))
        self._populate()
        name = D.THEME_NAMES[lv.theme]
        self.say(f"{name}, level {depth}" if depth < 50 else "Diablo's Sanctum. The Lord of Terror awaits.",
                 "#F0C060")

    def _place(self, spot):
        self.player.x, self.player.y = spot[0] + 0.5, spot[1] + 0.5

    def _town_people(self):
        lv = self.level
        people = [("smith", "Griswald the Smith", "smith"), ("witch", "Adria the Witch", "witch"),
                  ("healer", "Pepin the Healer", "healer"), ("elder", "Deckard the Elder", "elder")]
        for key, name, look in people:
            x, y = lv.places[key]
            self.npcs.append(NPC(x + 0.5, y + 0.5, key, name, look))

    def _restock(self):
        """New wares each visit to town, matched to your level."""
        rnd = random.Random(f"{self.seed}:{self.player.level}:{self.player.max_depth}:{int(self.time // 60)}")
        lvl = max(1, self.player.max_depth, self.player.level)
        smith = []
        for i in range(14):
            it = I.random_drop(lvl, rnd, kinds={"dagger", "sword", "axe", "mace", "bow", "armor", "helm", "shield"})
            if it["rarity"] == "rare":
                it = I.make(it["base"], it["ilvl"], "magic", rnd)
            it["ident"] = True
            smith.append(it)
        witch = [I.make(n) for n in ("Potion of Healing", "Potion of Mana", "Scroll of Town Portal",
                                     "Scroll of Identify")]
        if lvl >= 8:
            witch += [I.make("Potion of Full Healing"), I.make("Potion of Full Mana")]
        if lvl >= 14:
            witch.append(I.make("Potion of Rejuvenation"))
        for spell, (_m, _v, need, _d) in I.SPELLS.items():
            if need <= lvl + 2 and rnd.random() < 0.6:
                witch.append(I.make(f"Book of {spell}"))
        for _ in range(4):
            it = I.random_drop(lvl, rnd, kinds={"staff", "ring", "amulet"})
            if it["rarity"] == "rare":
                it = I.make(it["base"], it["ilvl"], "magic", rnd)
            it["ident"] = True
            witch.append(it)
        healer = [I.make("Potion of Healing"), I.make("Potion of Full Healing")] if lvl >= 6 else \
            [I.make("Potion of Healing")]
        self.shop_stock = {"smith": smith, "witch": witch, "healer": healer}

    def _populate(self):
        lv, rnd, depth = self.level, random.Random(f"{self.seed}:{self.depth}:m{self.time:.0f}"), self.depth
        p = self.player
        floors = [f for f in lv.floors() if math.hypot(f[0] - p.x, f[1] - p.y) > 8]
        if lv.theme == "sanctum":
            dx, dy = lv.places["diablo"]
            if not self.flags.get("diablo_dead"):
                self.monsters.append(Monster(dx + 0.5, dy + 0.5, "diablo", 50, rnd))
            for _ in range(4):
                fx, fy = rnd.choice([f for f in floors if math.hypot(f[0] - dx, f[1] - dy) < 9])
                self.monsters.append(Monster(fx + 0.5, fy + 0.5, "knight", 49, rnd))
            return
        kinds = THEME_MONSTERS[lv.theme]
        packs = 9 + depth // 4
        for _ in range(packs):
            if not floors:
                break
            cx, cy = rnd.choice(floors)
            kind = rnd.choice(kinds)
            n = rnd.randint(4, 7) if kind == "fallen" else rnd.randint(2, 4) if kind != "pitlord" else rnd.randint(1, 2)
            for i in range(n):
                for _try in range(10):
                    x, y = cx + rnd.randint(-2, 2), cy + rnd.randint(-2, 2)
                    if lv.floor(x, y):
                        break
                else:
                    continue
                self.monsters.append(Monster(x + 0.5, y + 0.5, kind, depth + rnd.randint(0, 1), rnd))
        if depth >= 3:
            for _ in range(rnd.randint(1, 2)):
                x, y = rnd.choice(floors)
                self.monsters.append(Monster(x + 0.5, y + 0.5, rnd.choice(kinds), depth + 1, rnd, champion=True))
        if depth in BOSSES:
            x, y = lv.down if lv.down else rnd.choice(floors)
            x, y = D._near_free(lv, (x, y))
            kind = {5: "ghoul", 15: "skeleton", 25: "magma", 35: "knight", 45: "pitlord"}[depth]
            self.monsters.append(Monster(x + 0.5, y + 0.5, kind, depth + 2, rnd, boss=BOSSES[depth]))
            self.say("You feel a terrible presence on this level...", "#FF8060")
        # chests, barrels, shrines
        for _ in range(rnd.randint(2, 4)):
            x, y = rnd.choice(floors)
            self.objects.append(Obj("chest", x + 0.5, y + 0.5))
        for _ in range(rnd.randint(6, 12)):
            x, y = rnd.choice(lv.floors())
            if (x, y) not in (lv.up, lv.down):
                self.objects.append(Obj("barrel", x + 0.5, y + 0.5))
        if rnd.random() < 0.75:
            x, y = rnd.choice(floors)
            name, colour = rnd.choice(SHRINES)
            self.objects.append(Obj("shrine", x + 0.5, y + 0.5, name=name, colour=colour))
        for _ in range(rnd.randint(2, 5)):
            x, y = rnd.choice(floors)
            self.ground.append(GroundItem(x + 0.5, y + 0.5, {"base": "Gold", "gold": rnd.randint(5, 20) * depth}))

    def take_stairs(self, obj):
        if obj.kind == "stairs_down":
            if self.depth >= 50:
                return
            self.enter(self.depth + 1, "up")
        elif obj.kind == "stairs_up":
            if self.depth == 1:
                self.enter(0, "down")
            else:
                self.enter(self.depth - 1, "down")

    def waystone_depths(self):
        out = [1]
        out += [d for d in range(5, 51, 5) if d <= self.player.max_depth]
        return out

    # ---- player commands -------------------------------------------------------------------------------
    def move_to(self, tx, ty):
        p = self.player
        p.target = None
        if not self.level.floor(tx, ty):
            return
        p.path = D.path(self.level, p.tile(), (tx, ty))

    def attack(self, m):
        self.player.target = m
        self.player.path = []

    def interact(self, thing):
        self.player.target = thing
        self.player.path = D.path(self.level, self.player.tile(), (int(thing.x), int(thing.y))) or []

    def cast(self, tx, ty):
        p = self.player
        spell = p.active_spell
        if not spell or p.anim > 0 or self.dead:
            return
        cost = I.SPELLS[spell][0]
        if p.mana < cost:
            self.say("Not enough mana.", "#8090FF")
            return
        if spell == "Town Portal" and self.depth == 0:
            return
        p.mana -= cost
        p.anim = 0.45
        p.pose = "cast"
        p.path = []
        d = self._face(tx, ty)
        self._spell(spell, p.spells.get(spell, 1) + p.spell_bonus, tx, ty, d)

    def _face(self, tx, ty):
        p = self.player
        dx, dy = tx - p.x, ty - p.y
        f = facing_for(dx, dy)
        if f is not None:
            p.facing = f
        return dx, dy

    def use_belt(self, i):
        p = self.player
        it = p.belt[i]
        if it is None:
            return
        self._drink(it)
        p.belt[i] = None
        # refill the slot from the pack
        for j, x in enumerate(p.inv):
            if x and x["base"] == it["base"]:
                one = dict(x)
                one["qty"] = 1
                p.belt[i] = one
                x["qty"] -= 1
                if x["qty"] <= 0:
                    p.inv[j] = None
                break

    def _drink(self, it):
        p = self.player
        b = it["base"]
        if "Rejuvenation" in b:
            p.hp, p.mana = p.maxhp, p.maxmana
        elif "Full Healing" in b:
            p.hp = p.maxhp
        elif "Full Mana" in b:
            p.mana = p.maxmana
        elif "Healing" in b:
            p.hp = min(p.maxhp, p.hp + p.maxhp * 0.4 + 10)
        elif "Mana" in b:
            p.mana = min(p.maxmana, p.mana + p.maxmana * 0.4 + 10)
        self.fx("heal" if "Mana" not in b else "mana", x=p.x, y=p.y, ttl=0.6)

    def use_item(self, idx):
        """Right-click in the pack: drink, read, or put on."""
        p = self.player
        it = p.inv[idx]
        if it is None:
            return
        k = I.kind(it)
        if k == "potion":
            self._drink(it)
            it["qty"] -= 1
            if it["qty"] <= 0:
                p.inv[idx] = None
        elif it["base"] == "Scroll of Town Portal":
            if self.depth == 0:
                self.say("You're already in town.")
                return
            self._open_portal()
            p.take_one(it["base"])
        elif it["base"] == "Scroll of Identify":
            target = next((x for x in p.inv if x and not x.get("ident", True)), None)
            if target is None:
                self.say("Everything you carry is already identified.")
                return
            target["ident"] = True
            p.take_one(it["base"])
            self.say(f"Identified: {I.name(target)}", I.colour(target))
        elif k == "book":
            spell = it["base"][8:]
            need = I.SPELLS[spell][2] // 2 + 10
            if p.mag < need:
                self.say(f"You need {need} Magic to learn {spell}.", "#FF8080")
                return
            p.spells[spell] = p.spells.get(spell, 0) + 1
            if p.active_spell is None:
                p.active_spell = spell
            p.inv[idx] = None
            self.say(f"You learn {spell} (level {p.spells[spell]}).", "#80C0FF")
        else:
            self.equip_from(idx)

    def equip_from(self, idx):
        p = self.player
        it = p.inv[idx]
        s = I.slot(it) if it else None
        if s is None:
            return False
        if not p.can_equip(it):
            self.say("You don't meet the requirements for that.", "#FF8080")
            return False
        if s == "ring":
            s = "ring1" if p.equip["ring1"] is None or p.equip["ring2"] is not None else "ring2"
        old = p.equip[s]
        p.equip[s] = it
        p.inv[idx] = old
        if s == "weapon" and I.two_handed(it) and p.equip["shield"]:
            if not p.add_item(p.equip["shield"]):
                self.drop_item(p.equip["shield"])
            p.equip["shield"] = None
        if s == "shield" and p.equip["weapon"] and I.two_handed(p.equip["weapon"]):
            if not p.add_item(p.equip["weapon"]):
                self.drop_item(p.equip["weapon"])
            p.equip["weapon"] = None
        p.recalc()
        return True

    def unequip(self, slot_name):
        p = self.player
        it = p.equip[slot_name]
        if it and p.add_item(it):
            p.equip[slot_name] = None
            p.recalc()

    def drop_item(self, item):
        p = self.player
        self.ground.append(GroundItem(p.x + random.uniform(-0.4, 0.4), p.y + random.uniform(-0.4, 0.4), item))

    def _open_portal(self):
        p = self.player
        self.portal = (self.depth, p.x + 0.8, p.y + 0.8)
        self.objects = [o for o in self.objects if o.kind != "portal"]
        self.objects.append(Obj("portal", *self.portal[1:]))
        self.say("A portal to town opens.", "#80C0FF")
        self.fx("flash", x=self.portal[1], y=self.portal[2], colour="#80C0FF", ttl=0.6)

    # ---- the frame -------------------------------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if self.dead:
            return
        p = self.player
        for k in list(p.buffs):
            p.buffs[k] -= dt
            if p.buffs[k] <= 0:
                del p.buffs[k]
                p.recalc()
        p.hp = min(p.maxhp, p.hp + (p.regen + 0.15) * dt)
        p.mana = min(p.maxmana, p.mana + (0.35 + p.mag / 200) * dt)
        p.cool = max(0.0, p.cool - dt)
        p.hurt = max(0.0, p.hurt - dt)
        if p.anim > 0:
            p.anim -= dt
            if p.hit_pending and p.anim <= p.hit_pending[0]:
                _t, target = p.hit_pending
                p.hit_pending = None
                self._player_strike(target)
            if p.anim <= 0:
                p.pose = "stand"
        else:
            self._player_act(dt)
        self._explore()
        for m in self.monsters:
            if not m.dead:
                self._monster(m, dt)
            else:
                m.anim += dt
        self.monsters = [m for m in self.monsters if not m.dead or m.anim < 30]
        for ms in self.missiles:
            self._missile(ms, dt)
        self.missiles = [m for m in self.missiles if not m.dead]
        for n in self.npcs:
            self._npc(n, dt)
        self.effects = [e for e in self.effects if self.time - e["t0"] < e["ttl"]]
        # gold underfoot
        for g in list(self.ground):
            if g.item.get("base") == "Gold" and math.hypot(g.x - p.x, g.y - p.y) < 0.7:
                p.gold += g.item["gold"]
                self.ground.remove(g)
                self.fx("text", x=g.x, y=g.y, text=f"{g.item['gold']} gold", colour="#F8D040", ttl=1.0)

    def _explore(self):
        p = self.player
        r = p.light
        px, py = int(p.x), int(p.y)
        for y in range(py - r, py + r + 1):
            for x in range(px - r, px + r + 1):
                if (x - px) ** 2 + (y - py) ** 2 <= r * r:
                    self.explored.add((x, y))

    def _walk(self, a, dt, speed):
        """Move an actor along its path. Returns True while still walking."""
        if not a.path:
            return False
        tx, ty = a.path[0][0] + 0.5, a.path[0][1] + 0.5
        dx, dy = tx - a.x, ty - a.y
        d = math.hypot(dx, dy)
        step = speed * dt
        if d <= step:
            a.x, a.y = tx, ty
            a.path.pop(0)
        else:
            a.x += dx / d * step
            a.y += dy / d * step
        f = facing_for(dx, dy)
        if f is not None:
            a.facing = f
        a.pose = "walk"
        a.phase += dt * speed * 2.2
        return True

    def _player_act(self, dt):
        p = self.player
        t = p.target
        if t is not None:
            if isinstance(t, Monster):
                if t.dead:
                    p.target = None
                else:
                    d = dist(p, t)
                    if p.ranged and d <= 9 and self._los(p, t):
                        self._player_swing(t)
                        return
                    if not p.ranged and d <= 1.45:
                        self._player_swing(t)
                        return
                    p.repath_t -= dt
                    if not p.path or p.repath_t <= 0:
                        p.path = D.path(self.level, p.tile(), t.tile())[:-1] or p.path
                        p.repath_t = 0.35
            else:
                if math.hypot(t.x - p.x, t.y - p.y) <= 1.3:
                    p.target = None
                    p.path = []
                    self._use(t)
                    return
        if not self._walk(p, dt, p.speed):
            p.pose = "stand"

    def _player_swing(self, m):
        p = self.player
        p.path = []
        if p.cool > 0:
            p.pose = "stand"
            return
        self._face(m.x, m.y)
        p.cool = p.swing
        p.anim = min(0.45, p.swing * 0.5)
        p.pose = "attack"
        p.phase = 0
        if p.ranged:
            self.missiles.append(Missile("arrow", p.x, p.y, m.x - p.x, m.y - p.y, 13, self._roll_player_damage(),
                                         "player", radius=0.4, life=1.2))
        else:
            p.hit_pending = (p.anim * 0.4, m)

    def _roll_player_damage(self):
        p = self.player
        return random.uniform(*p.dmg) + p.elem

    def _player_strike(self, m):
        p = self.player
        if m.dead or dist(p, m) > 1.8:
            return
        if random.uniform(0, 100) > max(10, min(95, p.to_hit - m.ac * 0.5)):
            self.fx("text", x=m.x, y=m.y, text="miss", colour="#A0A0A0", ttl=0.6)
            return
        self._hurt_monster(m, self._roll_player_damage(), "phys")

    def _hurt_monster(self, m, dmg, elem="phys"):
        if m.dead:
            return
        if elem in m.res:
            dmg *= (1 - m.res[elem] / 100)
        m.hp -= dmg
        m.hurt = 0.18
        m.state = "chase"
        m.seen = True
        p = self.player
        if p.leech and elem == "phys":
            p.hp = min(p.maxhp, p.hp + dmg * p.leech / 100)
        self.fx("text", x=m.x, y=m.y, text=str(int(dmg)), colour="#FFFFFF" if elem == "phys" else "#FFB060",
                ttl=0.7)
        if m.kind == "fallen" and m.hp < m.maxhp * 0.35:
            m.flee = 3.0
        if m.hp <= 0:
            self._kill(m)

    def _kill(self, m):
        m.dead = True
        m.anim = 0.0
        m.pose = "dead"
        p = self.player
        p.xp += m.xp
        self._drops(m)
        if m.kind == "diablo":
            self.flags["diablo_dead"] = True
            self.won_at = self.time
            self.say("Diablo, the Lord of Terror, is slain!", "#F0C060")
            for m2 in self.monsters:
                if not m2.dead:
                    self._kill(m2)
        elif m.boss:
            self.say(f"{m.name} is dead!", "#F0C060")
        while p.xp >= p.next_level_xp():
            p.xp -= p.next_level_xp()
            p.level += 1
            p.points += 5
            p.recalc()
            p.hp, p.mana = p.maxhp, p.maxmana
            self.say(f"You have reached level {p.level}! (5 points to spend - press C)", "#F0C060")
            self.fx("level", x=p.x, y=p.y, ttl=1.2)

    def _drops(self, m):
        rnd = random
        ilvl = max(1, m.mlevel)
        n_items = 3 if m.boss else 1 if m.champion else (1 if rnd.random() < 0.16 else 0)
        for i in range(n_items):
            it = I.random_drop(ilvl + (2 if m.boss else 0), rnd, magic_find=0.6 if m.boss or m.champion else 0)
            if (m.boss or m.champion) and it["rarity"] == "normal":
                it = I.make(it["base"], it["ilvl"], "rare" if m.boss and i == 0 else "magic", rnd)
            self._drop(m.x, m.y, it)
        if rnd.random() < (1.0 if m.boss else 0.4):
            self._drop(m.x, m.y, {"base": "Gold", "gold": int(rnd.randint(3, 12) * ilvl * (5 if m.boss else 1))})
        if rnd.random() < 0.12:
            self._drop(m.x, m.y, I.random_supply(ilvl, rnd))

    def _drop(self, x, y, item):
        for _ in range(12):
            nx, ny = x + random.uniform(-0.9, 0.9), y + random.uniform(-0.9, 0.9)
            if self.level.walkable(nx, ny):
                break
        else:
            nx, ny = x, y
        self.ground.append(GroundItem(nx, ny, item))

    # ---- using things -----------------------------------------------------------------------------------
    def _use(self, t):
        p = self.player
        if isinstance(t, GroundItem):
            if t in self.ground:
                if t.item.get("base") == "Gold":
                    p.gold += t.item["gold"]
                    self.ground.remove(t)
                elif (I.kind(t.item) == "potion" and p.belt_add(t.item)) or p.add_item(t.item):
                    self.ground.remove(t)
                else:
                    self.say("Your pack is full.", "#FF8080")
            return
        if isinstance(t, NPC):
            self.talk_to = t
            return
        if not isinstance(t, Obj):
            return
        if t.kind in ("stairs_down", "stairs_up"):
            self.take_stairs(t)
        elif t.kind == "portal":
            if self.depth == 0:
                d = self.portal[0]
                self.enter(d, "portal")
                self.portal = None
                self.objects = [o for o in self.objects if o.kind != "portal"]
            else:
                self.enter(0, "portal")
        elif t.kind == "waystone":
            self.waystone_open = True
        elif t.kind == "chest" and not t.opened:
            t.opened = True
            for _ in range(random.randint(1, 3)):
                if random.random() < 0.6:
                    self._drop(t.x, t.y, I.random_drop(self.depth, random))
                else:
                    self._drop(t.x, t.y, {"base": "Gold", "gold": random.randint(8, 25) * self.depth})
        elif t.kind == "barrel" and not t.opened:
            t.opened = True
            r = random.random()
            if self.level.theme in ("hell", "abyss", "caves") and r < 0.15:
                self.fx("explosion", x=t.x, y=t.y, r=1.6, colour="#FF8020", ttl=0.5)
                for m in self.monsters:
                    if not m.dead and math.hypot(m.x - t.x, m.y - t.y) < 1.8:
                        self._hurt_monster(m, 6 * self.depth, "fire")
                if math.hypot(p.x - t.x, p.y - t.y) < 1.8:
                    self._hurt_player(4 * self.depth, "fire", "An exploding barrel")
            elif r < 0.45:
                self._drop(t.x, t.y, {"base": "Gold", "gold": random.randint(2, 10) * self.depth})
            elif r < 0.6:
                self._drop(t.x, t.y, I.random_supply(self.depth, random))
        elif t.kind == "shrine" and not t.opened:
            t.opened = True
            self._shrine(t)

    def _shrine(self, t):
        p = self.player
        name = t.name
        msg = {"Glimmering Shrine": "Your items glimmer - you know their secrets.",
               "Divine Shrine": "Divine light restores you.",
               "Eerie Shrine": "You feel your mind sharpen. (+2 Magic)",
               "Abandoned Shrine": "You feel more agile. (+2 Dexterity)",
               "Creepy Shrine": "You feel stronger. (+2 Strength)",
               "Quiet Shrine": "You feel hardier. (+2 Vitality)",
               "Hidden Shrine": "Your armor shimmers. (+50% armor for two minutes)",
               "Ornate Shrine": "Arcane power fills you. (spells hit harder for two minutes)",
               "Gloomy Shrine": "Your weapon feels heavier. (+30% damage for two minutes)",
               "Fascinating Shrine": "Your magic grows deeper."}[name]
        if name == "Glimmering Shrine":
            for it in p.inv:
                if it:
                    it["ident"] = True
        elif name == "Divine Shrine":
            p.hp, p.mana = p.maxhp, p.maxmana
        elif name in ("Eerie Shrine", "Abandoned Shrine", "Creepy Shrine", "Quiet Shrine"):
            stat = {"Eerie Shrine": "mag", "Abandoned Shrine": "dex", "Creepy Shrine": "str", "Quiet Shrine": "vit"}
            p.base[stat[name]] += 2
        elif name in ("Hidden Shrine", "Ornate Shrine", "Gloomy Shrine"):
            p.buffs[name] = 120
        elif name == "Fascinating Shrine":
            if p.spells:
                s = random.choice(list(p.spells))
                p.spells[s] += 1
                msg = f"Your magic grows deeper. ({s} level {p.spells[s]})"
            else:
                p.base["mag"] += 3
                msg = "Your mind opens. (+3 Magic)"
        p.recalc()
        self.say(f"{name}: {msg}", t.colour)
        self.fx("flash", x=t.x, y=t.y, colour=t.colour, ttl=0.8)

    # ---- spells ------------------------------------------------------------------------------------------
    def _spell(self, spell, lvl, tx, ty, d):
        p = self.player
        power = (1 + 0.25 * (lvl - 1)) * (1.5 if p.buffs.get("Ornate Shrine") else 1.0)
        mag = p.mag
        if spell == "Firebolt":
            dmg = (random.uniform(3, 9) + mag / 4) * power
            self.missiles.append(Missile("firebolt", p.x, p.y, *d, 11, dmg, "player", "fire", life=1.4))
        elif spell == "Healing":
            p.hp = min(p.maxhp, p.hp + (15 + p.level * 3 + mag / 3) * power)
            self.fx("heal", x=p.x, y=p.y, ttl=0.7)
        elif spell == "Lightning":
            self._bolt(p.x, p.y, d, 9, (random.uniform(4, 16) + mag / 3) * power, "player")
        elif spell == "Fireball":
            dmg = (random.uniform(10, 24) + mag / 2.5) * power
            self.missiles.append(Missile("fireball", p.x, p.y, *d, 9, dmg, "player", "fire", radius=0.5, life=1.6))
        elif spell == "Chain Lightning":
            self._chain((random.uniform(8, 22) + mag / 2.5) * power, tx, ty)
        elif spell == "Nova":
            dmg = (random.uniform(12, 26) + mag / 2) * power
            self.fx("nova", x=p.x, y=p.y, r=5, colour="#A0C8FF", ttl=0.5)
            for m in self.monsters:
                if not m.dead and dist(m, p) < 5.2:
                    self._hurt_monster(m, dmg, "light")
        elif spell == "Inferno":
            for i in range(4):
                n = math.hypot(*d) or 1
                fx, fy = p.x + d[0] / n * (1 + i * 0.9), p.y + d[1] / n * (1 + i * 0.9)
                self.fx("flame", x=fx, y=fy, ttl=0.5)
                for m in self.monsters:
                    if not m.dead and math.hypot(m.x - fx, m.y - fy) < 0.9:
                        self._hurt_monster(m, (random.uniform(4, 10) + mag / 5) * power, "fire")
        elif spell == "Teleport":
            if self.level.walkable(tx, ty) and (int(tx), int(ty)) in self.explored:
                self.fx("flash", x=p.x, y=p.y, colour="#C080FF", ttl=0.4)
                p.x, p.y = int(tx) + 0.5, int(ty) + 0.5
                p.path = []
        elif spell == "Town Portal":
            self._open_portal()

    def _bolt(self, x, y, d, length, dmg, owner, elem="light", colour="#C0E0FF"):
        n = math.hypot(*d) or 1
        ux, uy = d[0] / n, d[1] / n
        pts = [(x, y)]
        hit = set()
        steps = int(length * 3)
        for i in range(1, steps + 1):
            cx, cy = x + ux * i / 3, y + uy * i / 3
            if self.level.wall(int(cx), int(cy)):
                break
            pts.append((cx + random.uniform(-0.15, 0.15), cy + random.uniform(-0.15, 0.15)))
            if owner == "player":
                for m in self.monsters:
                    if not m.dead and id(m) not in hit and math.hypot(m.x - cx, m.y - cy) < 0.6:
                        hit.add(id(m))
                        self._hurt_monster(m, dmg, elem)
            elif math.hypot(self.player.x - cx, self.player.y - cy) < 0.5 and "p" not in hit:
                hit.add("p")
                self._hurt_player(dmg, elem, "Lightning")
        self.fx("bolt", pts=pts, colour=colour, ttl=0.25)

    def _chain(self, dmg, tx, ty):
        p = self.player
        live = [m for m in self.monsters if not m.dead and dist(m, p) < 10 and self._los(p, m)]
        if not live:
            return
        cur = min(live, key=lambda m: math.hypot(m.x - tx, m.y - ty))
        pts = [(p.x, p.y)]
        done = []
        for _ in range(4):
            pts.append((cur.x, cur.y))
            done.append(cur)
            self._hurt_monster(cur, dmg, "light")
            nxt = [m for m in live if m not in done and not m.dead and dist(m, cur) < 5]
            if not nxt:
                break
            cur = min(nxt, key=lambda m: dist(m, cur))
        self.fx("bolt", pts=pts, colour="#D0E8FF", ttl=0.3)

    # ---- monsters -----------------------------------------------------------------------------------------
    def _los(self, a, b):
        x0, y0, x1, y1 = a.x, a.y, b.x, b.y
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
        for i in range(1, n):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            if self.level.wall(int(x), int(y)):
                return False
        return True

    def _monster(self, m, dt):
        p = self.player
        m.hurt = max(0.0, m.hurt - dt)
        m.cool = max(0.0, m.cool - dt)
        m.special = max(0.0, m.special - dt)
        m.flee = max(0.0, m.flee - dt)
        if m.anim > 0:
            m.anim -= dt
            if m.anim <= 0:
                m.pose = "stand"
            return
        d = dist(m, p)
        if d > 18:
            return
        if m.state == "idle":
            aggro = 7 if m.ai != "stealth" else 4
            if d < aggro and self._los(m, p):
                m.state = "chase"
                m.seen = True
                if m.boss:
                    self.say(f"{m.name}: " + ("Ah... fresh meat!" if "Butcher" in m.name else
                                             "Not even death can save you from me." if m.kind == "diablo" else
                                             "You dare enter my domain?"), "#FF8060")
            else:
                return
        if m.flee > 0:
            m.path = []
            self._step_away(m, p, dt)
            return
        if m.kind == "diablo":
            self._diablo(m, d, dt)
            return
        if m.ai in ("ranged", "caster") and d < 8 and self._los(m, p):
            if d < 3 and m.ai == "ranged":
                self._step_away(m, p, dt)
                return
            if m.cool <= 0:
                m.cool = 2.2 if m.ai == "ranged" else 3.0
                m.anim = 0.4
                m.pose = "attack" if m.ai == "ranged" else "cast"
                f = facing_for(p.x - m.x, p.y - m.y)
                if f is not None:
                    m.facing = f
                kind = m.missile
                dmg = random.uniform(*m.dmg) * (1.3 if kind == "fireball" else 1.0)
                elem = "fire" if kind in ("firebolt", "fireball") else "phys"
                self.missiles.append(Missile(kind, m.x, m.y, p.x - m.x, p.y - m.y, 8 if kind != "arrow" else 11,
                                             dmg, "monster", elem, radius=0.45, life=1.6))
            if m.ai == "caster" and d > 2:
                return
        if d <= 1.25 and m.ai != "ranged":
            m.path = []
            if m.cool <= 0:
                m.cool = 1.3
                m.anim = 0.4
                m.pose = "attack"
                f = facing_for(p.x - m.x, p.y - m.y)
                if f is not None:
                    m.facing = f
                self._monster_hit(m)
            return
        # chase
        m.repath -= dt
        if m.ai == "erratic":
            m.zig += dt * 3
            ang = math.atan2(p.y - m.y, p.x - m.x) + math.sin(m.zig) * 1.1
            nx, ny = m.x + math.cos(ang) * m.speed * dt, m.y + math.sin(ang) * m.speed * dt
            if self.level.walkable(nx, ny):
                m.x, m.y = nx, ny
            m.pose = "walk"
            m.phase += dt * 6
            return
        if self._los(m, p) and d < 6:
            m.path = []
            self._step_toward(m, p.x, p.y, dt)
        else:
            if m.repath <= 0 or not m.path:
                m.repath = 0.8
                m.path = D.path(self.level, m.tile(), p.tile(), limit=900)[:-1]
            if not self._walk(m, dt, m.speed):
                m.pose = "stand"
        self._separate(m)

    def _step_toward(self, m, tx, ty, dt):
        dx, dy = tx - m.x, ty - m.y
        d = math.hypot(dx, dy) or 1
        nx, ny = m.x + dx / d * m.speed * dt, m.y + dy / d * m.speed * dt
        if self.level.walkable(nx, m.y):
            m.x = nx
        if self.level.walkable(m.x, ny):
            m.y = ny
        f = facing_for(dx, dy)
        if f is not None:
            m.facing = f
        m.pose = "walk"
        m.phase += dt * m.speed * 2.2

    def _step_away(self, m, p, dt):
        self._step_toward(m, m.x * 2 - p.x, m.y * 2 - p.y, dt)

    def _separate(self, m):
        for o in self.monsters:
            if o is not m and not o.dead:
                dx, dy = m.x - o.x, m.y - o.y
                d = math.hypot(dx, dy)
                if 0 < d < 0.6:
                    push = (0.6 - d) * 0.5
                    nx, ny = m.x + dx / d * push, m.y + dy / d * push
                    if self.level.walkable(nx, ny):
                        m.x, m.y = nx, ny

    def _monster_hit(self, m):
        p = self.player
        chance = max(10, min(95, m.to_hit - p.ac * 0.25))
        if random.uniform(0, 100) > chance:
            return
        if p.block and random.uniform(0, 100) < p.block:
            self.fx("text", x=p.x, y=p.y, text="blocked", colour="#C0C0FF", ttl=0.6)
            return
        self._hurt_player(random.uniform(*m.dmg), "phys", m.name)
        if p.thorns:
            self._hurt_monster(m, p.thorns, "phys")

    def _hurt_player(self, dmg, elem, source):
        p = self.player
        if elem == "fire":
            dmg *= 1 - p.res_fire / 100
        elif elem == "light":
            dmg *= 1 - p.res_light / 100
        p.hp -= dmg
        p.hurt = 0.25
        if p.hp <= 0 and not self.dead:
            p.hp = 0
            self.dead = True
            p.pose = "dead"
            self.say(f"You have been slain by {source}.", "#FF4040")

    def _diablo(self, m, d, dt):
        p = self.player
        if m.special <= 0 and d < 9:
            m.special = 7.0
            m.anim = 0.6
            m.pose = "cast"
            if random.random() < 0.5:                      # fire nova
                self.fx("nova", x=m.x, y=m.y, r=6, colour="#FF6020", ttl=0.6)
                if d < 6:
                    self._hurt_player(random.uniform(40, 80), "fire", "Diablo's firestorm")
            else:                                          # red lightning
                for spread in (-0.3, 0, 0.3):
                    ang = math.atan2(p.y - m.y, p.x - m.x) + spread
                    self._bolt(m.x, m.y, (math.cos(ang), math.sin(ang)), 10, random.uniform(35, 70), "monster",
                               "light", "#FF4040")
            if m.hp < m.maxhp * 0.5 and not getattr(m, "summoned", False):
                m.summoned = True
                for _ in range(3):
                    self.monsters.append(Monster(m.x + random.uniform(-2, 2), m.y + random.uniform(-2, 2), "knight",
                                                 50, random, champion=True))
                self.say("Diablo calls his minions!", "#FF6040")
            return
        if d <= 1.8:
            if m.cool <= 0:
                m.cool = 1.2
                m.anim = 0.45
                m.pose = "attack"
                self._monster_hit(m)
            return
        self._step_toward(m, p.x, p.y, dt)

    def _missile(self, ms, dt):
        ms.life -= dt
        if ms.life <= 0:
            ms.dead = True
            if ms.kind == "fireball":
                self._explode(ms)
            return
        ms.x += ms.vx * dt
        ms.y += ms.vy * dt
        if self.level.wall(int(ms.x), int(ms.y)):
            ms.dead = True
            if ms.kind == "fireball":
                self._explode(ms)
            return
        if ms.owner == "player":
            for m in self.monsters:
                if not m.dead and id(m) not in ms.hit and math.hypot(m.x - ms.x, m.y - ms.y) < ms.radius + 0.25:
                    if ms.kind == "fireball":
                        ms.dead = True
                        self._explode(ms)
                        return
                    hit_chance = max(10, min(95, self.player.to_hit - m.ac * 0.5)) if ms.kind == "arrow" else 100
                    ms.hit.add(id(m))
                    if random.uniform(0, 100) <= hit_chance:
                        self._hurt_monster(m, ms.dmg, ms.elem)
                    ms.dead = True
                    return
        else:
            p = self.player
            if math.hypot(p.x - ms.x, p.y - ms.y) < ms.radius + 0.2:
                ms.dead = True
                if ms.kind == "fireball":
                    self._explode(ms)
                    return
                if p.block and ms.kind == "arrow" and random.uniform(0, 100) < p.block:
                    self.fx("text", x=p.x, y=p.y, text="blocked", colour="#C0C0FF", ttl=0.6)
                    return
                self._hurt_player(ms.dmg, ms.elem, "a missile")

    def _explode(self, ms):
        self.fx("explosion", x=ms.x, y=ms.y, r=1.5, colour="#FF8020", ttl=0.45)
        if ms.owner == "player":
            for m in self.monsters:
                if not m.dead and math.hypot(m.x - ms.x, m.y - ms.y) < 1.6:
                    self._hurt_monster(m, ms.dmg, "fire")
        elif math.hypot(self.player.x - ms.x, self.player.y - ms.y) < 1.5:
            self._hurt_player(ms.dmg, "fire", "a fireball")

    # ---- the townsfolk ---------------------------------------------------------------------------------------
    def _npc(self, n, dt):
        n.phase += dt
        if n.path:
            self._walk(n, dt, 1.0)
            return
        n.pose = "stand"
        n.wait -= dt
        if n.wait <= 0:
            n.wait = random.uniform(3, 8)
            hx, hy = n.home
            goal = (int(hx + random.randint(-2, 2)), int(hy + random.randint(-1, 2)))
            n.path = D.path(self.level, n.tile(), goal, limit=200)

    # ---- town services ---------------------------------------------------------------------------------------
    def heal(self):
        p = self.player
        p.hp, p.mana = p.maxhp, p.maxmana

    def identify_all(self):
        p = self.player
        todo = [it for it in p.inv + list(p.equip.values()) if it and not it.get("ident", True)]
        cost = 100 * len(todo)
        if not todo:
            return "You have nothing that needs identifying."
        if p.gold < cost:
            return f"That will cost {cost} gold, friend - and you have {p.gold}."
        p.gold -= cost
        for it in todo:
            it["ident"] = True
        return f"Let me see... ({len(todo)} item{'s' if len(todo) != 1 else ''} identified for {cost} gold)"

    def buy(self, shop, idx):
        p = self.player
        stock = self.shop_stock[shop]
        it = stock[idx]
        price = I.buy_price(it)
        if p.gold < price:
            return "You can't afford that."
        if not ((I.kind(it) == "potion" and p.belt_add(dict(it))) or p.add_item(dict(it))):
            return "Your pack is full."
        p.gold -= price
        if it["rarity"] != "supply":
            stock.pop(idx)
        return None

    def sell(self, idx):
        p = self.player
        it = p.inv[idx]
        if it is None:
            return
        price = I.sell_price(it) if it["rarity"] != "supply" else max(1, I.SUPPLIES[it["base"]][1] // 4)
        if it["rarity"] == "supply" and it["qty"] > 1:
            it["qty"] -= 1
        else:
            p.inv[idx] = None
        p.gold += price
        return price

    def revive(self):
        """After death: wake up in town with half your gold."""
        p = self.player
        lost = p.gold // 2
        p.gold -= lost
        self.dead = False
        p.hp, p.mana = p.maxhp, p.maxmana
        p.pose = "stand"
        self.portal = None
        self.enter(0)
        self.say(f"You wake in Haven. ({lost} gold was lost in the dark.)", "#FF8080")

    # ---- saving -------------------------------------------------------------------------------------------
    def to_json(self):
        return {"seed": self.seed, "player": self.player.to_json(), "depth": self.depth, "portal": self.portal,
                "flags": self.flags}

    @classmethod
    def from_json(cls, d):
        w = cls(d["seed"], Player.from_json(d["player"]))
        w.flags.update(d.get("flags", {}))
        w.portal = tuple(d["portal"]) if d.get("portal") else None
        if d.get("depth", 0) > 0:
            w.enter(d["depth"], "up")
        else:
            w.enter(0)
        return w
