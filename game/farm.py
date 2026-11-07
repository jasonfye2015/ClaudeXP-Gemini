"""Claude's farm plot, beside his cabin: plots that take a seed, grow over game days (a crop grows only on a day it
has been watered - by him, by the rain, or by the sprinkler), and ripen in four stages; a harvest gives the crop and
sometimes its seed back. The sign at the plot's foot runs it: planting, watering, harvesting, and the automation -
a sprinkler (waters every plot each morning), a farmhand (harvests what's ripe into the basket and plants again from
the seeds in the cabin's chest or his pack), and more plots.

    farm = Farm() / Farm.from_json(d)
    farm.grow(sky, minutes)            time going by (the world calls it every step, and when he sleeps)
    farm.plant(i, crop, day) / farm.water_all(day) / farm.harvest(i, rng) / farm.harvest_all(rng)"""
from . import food as F

START_PLOTS, MAX_PLOTS, PLOTS_PER_EXPANSION = 8, 20, 4
UPGRADES = {"sprinkler": ("Sprinkler", 300, "Waters every plot each morning."),
            "farmhand": ("Farmhand", 800, "Harvests what's ripe into the basket, and plants again from your seeds."),
            "expand": ("More plots", 500, "Four more plots, to twenty.")}


class Farm:
    def __init__(self):
        self.plots = [None for _ in range(START_PLOTS)]   # None, or {crop, growth 0..1, watered (game day)}
        self.upgrades = {}
        self.basket = {}                                  # what the farmhand has picked: larder keys -> counts
        self.replant = True

    # ---- growing ---------------------------------------------------------------------------------------------
    def grow(self, sky, minutes):
        day = sky.day
        rain = sky.now()["kind"] in ("rain", "storm") and sky.now()["strength"] > 0.2
        morning = self.upgrades.get("sprinkler") and sky.hour >= 6
        for p in self.plots:
            if not p:
                continue
            if rain or morning:
                p["watered"] = day
            if p["watered"] == day and p["growth"] < 1:
                days = F.CROPS[p["crop"]][1]
                p["growth"] = min(1.0, p["growth"] + minutes / (days * 1440))

    def stage(self, i):
        """0 sown, 1-3 growing, 4 ripe (the crop sheet's four stages after the sowing)."""
        p = self.plots[i]
        if not p:
            return None
        g = p["growth"]
        return 4 if g >= 1 else 0 if g < 0.12 else 1 + min(2, int((g - 0.12) / 0.3))

    def ripe(self, i):
        return bool(self.plots[i]) and self.plots[i]["growth"] >= 1

    # ---- working it ------------------------------------------------------------------------------------------
    def plant(self, i, crop, day):
        if self.plots[i] is not None or crop not in F.CROPS:
            return False
        self.plots[i] = {"crop": crop, "growth": 0.0, "watered": -1}
        return True

    def water_all(self, day):
        n = 0
        for p in self.plots:
            if p and p["watered"] != day:
                p["watered"] = day
                n += 1
        return n

    def harvest(self, i, rng):
        """-> {larder key: count} (the crop, and sometimes its seed), the plot emptied; {} if not ripe."""
        if not self.ripe(i):
            return {}
        crop = self.plots[i]["crop"]
        lo, hi = F.CROPS[crop][2]
        got = {f"raw:{crop}": rng.randint(lo, hi)}
        if rng.random() < F.CROPS[crop][3]:
            got[f"seed:{crop}"] = 1 + (1 if rng.random() < 0.3 else 0)
        self.plots[i] = None
        return got

    def harvest_all(self, rng):
        got = {}
        for i in range(len(self.plots)):
            for k, n in self.harvest(i, rng).items():
                got[k] = got.get(k, 0) + n
        return got

    def tend(self, rng, seeds, day):
        """The farmhand: what's ripe into the basket, and the plots sown again from seeds ({seed key: count}, taken
        from as it goes). -> True if anything was done."""
        if not self.upgrades.get("farmhand"):
            return False
        done = False
        for i in range(len(self.plots)):
            if self.ripe(i):
                crop = self.plots[i]["crop"]
                for k, n in self.harvest(i, rng).items():
                    self.basket[k] = self.basket.get(k, 0) + n
                done = True
                if self.replant:
                    key = f"seed:{crop}" if seeds.get(f"seed:{crop}", 0) > 0 else next((k for k, n in seeds.items() if n > 0), None)
                    if key:
                        seeds[key] -= 1
                        self.plant(i, key.split(":", 1)[1], day)
        return done

    def buy(self, key, player):
        name, cost, _what = UPGRADES[key]
        if player.gold < cost:
            return False
        if key == "expand":
            if len(self.plots) >= MAX_PLOTS:
                return False
            self.plots += [None] * PLOTS_PER_EXPANSION
        elif self.upgrades.get(key):
            return False
        else:
            self.upgrades[key] = True
        player.gold -= cost
        return True

    # ---- saving --------------------------------------------------------------------------------------------
    def to_json(self):
        return {"plots": self.plots, "upgrades": self.upgrades, "basket": self.basket, "replant": self.replant}

    @classmethod
    def from_json(cls, d):
        f = cls()
        if d:
            f.plots = d.get("plots", f.plots)
            f.upgrades = d.get("upgrades", {})
            f.basket = d.get("basket", {})
            f.replant = d.get("replant", True)
        return f
