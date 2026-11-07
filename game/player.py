"""Claude: his level and experience, his gold, what he carries and wears, his wands, potions and scrolls, and the
skill points he's put by. Everything here survives death (only the run - how deep he'd got - is lost)."""
from . import data as D
from . import items as I

INVENTORY_SIZE = 48


class Player:
    def __init__(self):
        # the farm and the kitchen (game/food.py): counts by key ("seed:carrot", "raw:meat", "cooked:stew")
        self.larder = {"seed:carrot": 3, "seed:potato": 2, "seed:radish": 2}
        self.stash = []                                      # the cabin's chest: items
        self.stash_larder = {}                               # and its larder
        self.buffs = []                                      # [recipe key, ends at (the wall clock's seconds)]
        self.cookbook = []                                   # the recipes found
        self.level = 1
        self.xp = 0
        self.gold = 30
        self.inventory = []                                  # items (dicts), in the order found
        self.gear = {s: None for s in D.GEAR_SLOTS}
        self.wands = [I.make_wand("birch")] + [None] * (D.WAND_SLOTS - 1)
        self.active = 0
        self.potions = {"health": 3, "mana": 2, "return": 1}
        self.skills = {}                                     # node id -> rank (game/skills.py; phase 3)
        self.skill_points = 0
        self.life = self.max_life()
        self.mana = self.max_mana()
        self.stats = {"kills": 0, "deaths": 0, "deepest": 0, "guardians": []}

    # ---- what he is, all told ------------------------------------------------------------------------------------
    def bonus(self):
        b = {}
        for g in self.gear.values():
            if g:
                for k, v in g["stats"].items():
                    b[k] = b.get(k, 0) + v
        try:
            from . import skills
            for k, v in skills.bonus(self.skills).items():
                b[k] = b.get(k, 0) + v
        except ImportError:
            pass
        from . import food
        for k, v in food.bonus(self.buffs).items():           # (the meals in him)
            b[k] = b.get(k, 0) + v
        return b

    def eat(self, key):
        """Eat one from the larder: raw heals a little; a cooked meal is a buff for its hours (real time), three at
        most (the oldest goes); the same meal again starts its time over. -> what it did, or None."""
        import time
        from . import food
        if self.larder.get(key, 0) <= 0:
            return None
        kind, _, k = key.partition(":")
        if kind == "seed":
            return None
        food.add(self.larder, key, -1)
        if kind == "raw":
            life, mana = food.RAW[k][2:] if k in food.RAW else food.RAW_CROP
            self.life = min(self.max_life(), self.life + self.max_life() * life)
            self.mana = min(self.max_mana(), self.mana + self.max_mana() * mana)
            return f"Claude eats the {food.name_of(key).lower()}. It does him a little good."
        r = food.RECIPES[k]
        now = time.time()
        self.buffs = [[b, t] for b, t in food.active(self.buffs, now) if b != k]
        if len(self.buffs) >= food.MAX_BUFFS:              # (the one eaten longest ago goes)
            self.buffs = self.buffs[1:]
        self.buffs.append([k, now + r[4] * 3600])
        self.life = min(self.max_life(), self.life + self.max_life() * 0.15)
        return f"{r[0]}: " + ", ".join(food.buff_lines(r[3])) + f" for {r[4]} hour{'s' if r[4] != 1 else ''}."

    def max_life(self):
        b = self.bonus()
        return int((60 + 11 * (self.level - 1) + b.get("life", 0)) * (1 + b.get("life%", 0) / 100))

    def max_mana(self):
        b = self.bonus()
        return int((40 + 5 * (self.level - 1) + b.get("mana", 0)) * (1 + b.get("mana%", 0) / 100))

    def mana_regen(self):
        return 4.0 + 0.12 * self.level + self.bonus().get("regen", 0)

    def armour(self):
        return 2 * self.level + self.bonus().get("armour", 0)

    def speed(self):
        return 3.4 * (1 + min(60, self.bonus().get("swift", 0)) / 100)

    def wand(self):
        w = self.wands[self.active]
        if w is None:
            w = next((x for x in self.wands if x), None)
        return w

    def wand_stats(self):
        w = self.wand()
        return I.wand_stats(w, self.bonus()) if w else None

    def damage_taken(self, raw):
        """What a blow of raw damage takes off, after armour (diminishing: 60 armour halves it, 180 quarters it)."""
        return max(1.0, raw * 60 / (60 + max(0, self.armour())))

    # ---- growing ----------------------------------------------------------------------------------------------
    def add_xp(self, n):
        """-> how many levels were gained"""
        self.xp += n
        gained = 0
        while self.xp >= I.xp_to_next(self.level):
            self.xp -= I.xp_to_next(self.level)
            self.level += 1
            self.skill_points += 1
            gained += 1
        if gained:
            self.life, self.mana = self.max_life(), self.max_mana()
        return gained

    # ---- carrying ---------------------------------------------------------------------------------------------
    def give(self, item):
        """Into the pack (or, if it's full, sold where it lies for what a vendor would give). -> True if kept"""
        if len(self.inventory) >= INVENTORY_SIZE:
            self.gold += I.sell_price(item)
            return False
        self.inventory.append(item)
        return True

    def equip(self, item):
        """Wear a piece of gear from the pack (what was worn goes back in its place)."""
        if item.get("type") != "gear" or item not in self.inventory:
            return False
        slot = item["slot"]
        i = self.inventory.index(item)
        old = self.gear[slot]
        self.gear[slot] = item
        if old:
            self.inventory[i] = old
        else:
            self.inventory.pop(i)
        self.life = min(self.life, self.max_life())
        self.mana = min(self.mana, self.max_mana())
        return True

    def unequip(self, slot):
        g = self.gear.get(slot)
        if not g or len(self.inventory) >= INVENTORY_SIZE:
            return False
        self.gear[slot] = None
        self.inventory.append(g)
        self.life = min(self.life, self.max_life())
        self.mana = min(self.mana, self.max_mana())
        return True

    def ready_wand(self, item, slot=None):
        """A wand from the pack into one of the four ready slots (whatever was there goes back to the pack)."""
        if item.get("type") != "wand" or item not in self.inventory:
            return False
        if slot is None:
            slot = next((k for k, w in enumerate(self.wands) if w is None), self.active)
        i = self.inventory.index(item)
        old = self.wands[slot]
        self.wands[slot] = item
        if old:
            self.inventory[i] = old
        else:
            self.inventory.pop(i)
        return True

    def set_part(self, wand, index, part):
        """Set a part from the pack into a wand's slot (the part already there goes back to the pack)."""
        if part is not None and (part.get("type") != "part" or part not in self.inventory):
            return False
        if not 0 <= index < len(wand["parts"]):
            return False
        old = wand["parts"][index]
        if part is not None:
            self.inventory.remove(part)
        wand["parts"][index] = part
        if old:
            self.inventory.append(old)
        return True

    # ---- saving -----------------------------------------------------------------------------------------------
    FIELDS = ("level", "xp", "gold", "inventory", "gear", "wands", "active", "potions", "skills", "skill_points",
              "life", "mana", "stats", "larder", "stash", "stash_larder", "buffs", "cookbook")

    def to_json(self):
        return {k: getattr(self, k) for k in self.FIELDS}

    @classmethod
    def from_json(cls, d):
        p = cls()
        for k in cls.FIELDS:
            if k in d:
                setattr(p, k, d[k])
        for s in D.GEAR_SLOTS:
            p.gear.setdefault(s, None)
        for it in list(p.inventory) + list(p.stash) + list(p.gear.values()) + list(p.wands):   # (older saves' things)
            I.migrate(it)
        while len(p.wands) < D.WAND_SLOTS:
            p.wands.append(None)
        if not any(p.wands):
            p.wands[0] = I.make_wand("birch")
        for k in ("health", "mana", "return"):
            p.potions.setdefault(k, 0)
        p.life = min(p.life, p.max_life())
        p.mana = min(p.mana, p.max_mana())
        return p
