"""ClaudePit's rules: a 5 x 3 slot machine at the bottom of a pit, after CloverPit.

Each deadline has three rounds. A round starts with buying spins (seven of them, or three and a Clover Ticket) with
the coins in your pocket; every spin pays for each pattern of matching symbols on the reels - a row of three or more,
a column, a diagonal, the zig and the zag, and the big ones up to a full-screen Jackpot. Coins only count once they're
in the ATM, which pays interest every round; 6-6-6 across the middle takes everything in your pocket. When a deadline's
third round is spent the ATM takes the debt - and if it isn't there, the trapdoor opens. Clover Tickets buy charms
from the machine on the wall; after each deadline paid, the phone rings with a choice of abilities, holy or evil.
Pay the tenth deadline to climb out (and the pit goes on, if you'd rather stay)."""
import math
import random

ROWS, COLS = 3, 5
SIX = "six"
SYMBOLS = ("lemon", "cherry", "clover", "bell", "diamond", "treasure", "seven")
SYMBOL_NAME = {"lemon": "Lemon", "cherry": "Cherry", "clover": "Clover", "bell": "Bell", "diamond": "Diamond",
               "treasure": "Treasure", "seven": "Seven", SIX: "Six"}
VALUE = {"lemon": 2, "cherry": 2, "clover": 3, "bell": 3, "diamond": 5, "treasure": 5, "seven": 7}
WEIGHT = {"lemon": 20, "cherry": 20, "clover": 15, "bell": 15, "diamond": 11, "treasure": 11, "seven": 8}

# key: (name, multiplier)
PATTERNS = {"h3": ("Horizontal", 1), "h4": ("Horizontal 4", 2), "h5": ("Horizontal 5", 3),
            "vertical": ("Vertical", 2), "diagonal": ("Diagonal", 2), "zig": ("Zig", 4), "zag": ("Zag", 4),
            "above": ("Above", 7), "below": ("Below", 7), "eye": ("Eye", 8), "jackpot": ("Jackpot", 10)}
ZIG = [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4)]          # a V
ZAG = [(2, 0), (1, 1), (0, 2), (1, 3), (2, 4)]          # a peak


def _shapes():
    out = [("vertical", [(r, c) for r in range(ROWS)]) for c in range(COLS)]
    for c in range(COLS - 2):
        out.append(("diagonal", [(0, c), (1, c + 1), (2, c + 2)]))
        out.append(("diagonal", [(2, c), (1, c + 1), (0, c + 2)]))
    out += [("zig", ZIG), ("zag", ZAG),
            ("above", sorted(set(ZAG) | {(2, c) for c in range(COLS)})),
            ("below", sorted(set(ZIG) | {(0, c) for c in range(COLS)})),
            ("eye", [(r, c) for r in range(ROWS) for c in range(COLS) if r == 1 or 0 < c < COLS - 1]),
            ("jackpot", [(r, c) for r in range(ROWS) for c in range(COLS)])]
    return out


SHAPES = _shapes()
SHAPE_OF = {"zig": ZIG, "zag": ZAG}                     # (for drawing the pattern table)
for _k, _cells in SHAPES:
    SHAPE_OF.setdefault(_k, _cells)
SHAPE_OF.update({"h3": [(1, 1), (1, 2), (1, 3)], "h4": [(1, 0), (1, 1), (1, 2), (1, 3)],
                 "h5": [(1, c) for c in range(COLS)], "vertical": [(0, 2), (1, 2), (2, 2)],
                 "diagonal": [(0, 1), (1, 2), (2, 3)]})

FINAL = 10                      # pay this many deadlines to climb out
ROUNDS = 3
START_COINS = 24
START_TICKETS = 2
BASE_666 = 0.015
BASE_INTEREST = 0.05
GROWTH = 1.6                    # what everything pays grows by this each deadline
COIN = 3.0                      # what a symbol's value is worth, in coins
PRICE_DIV = 30                  # a spin costs the debt / this
SLOTS = 6
MAX_SLOTS = 9


DEBT_BASE = 50
DEBT_RATE = 2.0


def debt_for(d):
    """Each deadline's debt (rounded to look like a bill)."""
    x = DEBT_BASE * DEBT_RATE ** (d - 1)
    step = 10 ** max(0, int(math.log10(x)) - 1)
    return int(round(x / step) * step)


# key: (name, price in tickets, what it does)
CHARMS = {
    "lemon_zest": ("Lemon Zest", 1, "Lemons are worth +2."),
    "cherry_pit": ("Cherry Pit", 1, "Cherries are worth +2."),
    "clover_pot": ("Clover Pot", 2, "Clovers are worth +3."),
    "brass_bell": ("Brass Bell", 2, "Bells are worth +3."),
    "loupe": ("Jeweler's Loupe", 3, "Diamonds are worth +4."),
    "pirate_map": ("Pirate Map", 3, "Treasure is worth +4."),
    "lucky_seven": ("Lucky Seven", 3, "Sevens are worth +5."),
    "horseshoe": ("Horseshoe", 3, "+3 Luck."),
    "rabbit_foot": ("Rabbit's Foot", 2, "+2 Luck, and 666 is half a percent less likely."),
    "fortune_cookie": ("Fortune Cookie", 2, "+1 Clover Ticket at the start of every round."),
    "piggy_bank": ("Piggy Bank", 3, "The ATM pays +5% more interest."),
    "golden_lever": ("Golden Lever", 2, "Every pull of the lever pays a coin (more in later deadlines)."),
    "magnifier": ("Magnifying Glass", 3, "Horizontal patterns: multiplier +1."),
    "plumb_bob": ("Plumb Bob", 2, "Vertical patterns: multiplier +2."),
    "slide_rule": ("Slide Rule", 2, "Diagonal patterns: multiplier +2."),
    "ribbon": ("Zigzag Ribbon", 3, "Zig and Zag: multiplier +3."),
    "crown": ("Paper Crown", 4, "Above, Below, Eye and Jackpot: multiplier +5."),
    "rosary": ("Rosary", 3, "666 is half as likely."),
    "hourglass": ("Hourglass", 4, "+1 spin every round."),
    "coupon": ("Coupon Book", 3, "Spins cost 25% less."),
    "die": ("Loaded Die", 3, "A 1 in 6 chance that a spin pays double."),
    "weighted_reels": ("Weighted Reels", 4, "Sevens come up far more often."),
    "fruit_basket": ("Fruit Basket", 2, "Lemons and Cherries come up more often."),
    "lucky_cat": ("Maneki-neko", 3, "Every pattern pays 2 coins more (more in later deadlines)."),
    "snake_eyes": ("Snake Eyes", 2, "Everything pays x1.5 - but 666 is 1% more likely."),
    "coin_purse": ("Coin Purse", 2, "Deposits earn a 10% bonus."),
    "rope_ladder": ("Rope Ladder", 5, "Miss a deadline once and live (then it snaps)."),
    "mirror": ("Hand Mirror", 4, "The best pattern of every spin pays twice."),
    "abacus": ("Abacus", 4, "Every pattern after the first in a spin adds +50% to that spin."),
    "wishing_well": ("Wishing Well", 3, "Every spin that pays nothing adds +25% to the next one that does."),
    "clover_field": ("Clover Field", 3, "+1 Clover Ticket whenever Clovers pay."),
    "red_phone": ("Red Telephone", 3, "The phone offers four abilities instead of three."),
    "magnet": ("Coin Magnet", 2, "A spin that pays nothing still pays 3 coins (more in later deadlines)."),
}
CHARM_VALUE = {"lemon_zest": ("lemon", 2), "cherry_pit": ("cherry", 2), "clover_pot": ("clover", 3),
               "brass_bell": ("bell", 3), "loupe": ("diamond", 4), "pirate_map": ("treasure", 4),
               "lucky_seven": ("seven", 5)}
CHARM_PATTERN = {"magnifier": (("h3", "h4", "h5"), 1), "plumb_bob": (("vertical",), 2),
                 "slide_rule": (("diagonal",), 2), "ribbon": (("zig", "zag"), 3),
                 "crown": (("above", "below", "eye", "jackpot"), 5)}


def fmt(n):
    n = int(n)
    if abs(n) >= 10_000_000:
        return f"{n / 1_000_000:.1f}M"
    return f"{n:,}"


class Run:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.deadline = 1
        self.round = 1
        self.debt = debt_for(1)
        self.debt_extra = 0.0           # (an evil call's: the next debt is bigger)
        self.bank = 0
        self.pocket = START_COINS
        self.tickets = START_TICKETS
        self.spins = 0
        self.stage = "package"          # package / spin / phone / dead / won
        self.luck = 0
        self.charms = []
        self.slots = SLOTS
        self.value_bonus = {s: 0 for s in SYMBOLS}
        self.weight_bonus = {s: 0 for s in SYMBOLS}
        self.pattern_bonus = {k: 0 for k in PATTERNS}
        self.pay_mult = 1.0
        self.interest = BASE_INTEREST
        self.risk = 0.0                 # added to the chance of 666
        self.store = []
        self.reroll_cost = 1
        self.offers = []
        self.abilities = []             # (kind, name) taken from the phone
        self.grid = [[self.rng.choice(SYMBOLS) for _c in range(COLS)] for _r in range(ROWS)]
        self.streak = 0
        self.ladder_used = False
        self.won = False
        self.endless = False
        self.cause = ""
        self.best_spin = 0
        self.total_won = 0
        self.spins_pulled = 0
        self.sixes = 0
        self.restock()

    # ---- what things are worth ----
    def has(self, key):
        return key in self.charms

    def growth(self):
        return GROWTH ** (self.deadline - 1)

    def value(self, s):
        v = VALUE[s] + self.value_bonus[s]
        for key, (sym, n) in CHARM_VALUE.items():
            if sym == s and self.has(key):
                v += n
        return v

    def weight(self, s):
        w = WEIGHT[s] + self.weight_bonus[s]
        if s == "seven" and self.has("weighted_reels"):
            w += 9
        if s in ("lemon", "cherry") and self.has("fruit_basket"):
            w += 10
        return max(1, w)

    def mult(self, key):
        m = PATTERNS[key][1] + self.pattern_bonus[key]
        for charm, (keys, n) in CHARM_PATTERN.items():
            if key in keys and self.has(charm):
                m += n
        return m

    def total_luck(self):
        return self.luck + 3 * self.has("horseshoe") + 2 * self.has("rabbit_foot")

    def chance_666(self):
        p = BASE_666 + self.risk + 0.01 * self.has("snake_eyes") - 0.005 * self.has("rabbit_foot")
        if self.has("rosary"):
            p /= 2
        return max(0.0, min(0.5, p))

    def payout_mult(self):
        return self.pay_mult * (1.5 if self.has("snake_eyes") else 1.0)

    def interest_rate(self):
        return self.interest + 0.05 * self.has("piggy_bank")

    def spin_price(self):
        p = self.debt / PRICE_DIV
        if self.has("coupon"):
            p *= 0.75
        return max(1, round(p))

    def packages(self):
        """[(label, spins, tickets, cost)] for this round."""
        extra = 1 if self.has("hourglass") else 0
        p = self.spin_price()
        out = [("Seven spins", 7 + extra, 0, 7 * p), ("Three spins and a ticket", 3 + extra, 1, 3 * p)]
        if self.pocket < min(c for *_x, c in out):
            out = [("Last chance: three spins, on the house", 3 + extra, 0, 0)]
        return out

    # ---- a round ----
    def start_round(self):
        gained = int(self.bank * self.interest_rate())
        self.bank += gained
        if self.has("fortune_cookie"):
            self.tickets += 1
        return gained

    def choose(self, i):
        options = self.packages()
        if self.stage != "package" or not 0 <= i < len(options):
            return False
        _label, n, t, cost = options[i]
        if cost > self.pocket:
            return False
        self.pocket -= cost
        self.tickets += t
        self.spins = n
        self.stage = "spin"
        return True

    def roll(self):
        rng = self.rng
        weights = [self.weight(s) for s in SYMBOLS]
        luck = min(0.5, self.total_luck() * 0.022)
        grid = [[None] * COLS for _r in range(ROWS)]
        for c in range(COLS):
            for r in range(ROWS):
                near = ([grid[r][c - 1]] if c else []) + ([grid[r - 1][c]] if r else [])
                if near and rng.random() < luck:
                    grid[r][c] = rng.choice(near)
                else:
                    grid[r][c] = rng.choices(SYMBOLS, weights)[0]
        return grid

    def find(self, grid):
        """The patterns on the reels: [(key, symbol, cells)]."""
        wins = []
        for r in range(ROWS):
            c = 0
            while c < COLS:
                s, e = grid[r][c], c
                while e + 1 < COLS and grid[r][e + 1] == s:
                    e += 1
                if e - c + 1 >= 3 and s != SIX:
                    wins.append((f"h{e - c + 1}", s, [(r, k) for k in range(c, e + 1)]))
                c = e + 1
        for key, cells in SHAPES:
            s = grid[cells[0][0]][cells[0][1]]
            if s != SIX and all(grid[r][c] == s for r, c in cells):
                wins.append((key, s, cells))
        return wins

    def spin(self):
        """Pull the lever. Returns what happened, for the reels to show."""
        if self.stage != "spin" or self.spins <= 0:
            return None
        rng = self.rng
        self.spins -= 1
        self.spins_pulled += 1
        g = self.growth()
        res = {"wins": [], "extras": [], "total": 0, "six": False, "lost": 0, "tickets": 0}
        lever = round(g) if self.has("golden_lever") else 0
        if rng.random() < self.chance_666():
            grid = self.roll()
            for c in (1, 2, 3):
                grid[1][c] = SIX
            self.grid = grid
            res.update(six=True, lost=self.pocket, grid=grid)
            self.pocket = 0
            self.sixes += 1
            self.streak = 0
            if lever:
                self.pocket += lever
                res["extras"].append(("Golden Lever", f"+{lever}"))
            self._after_spin(res)
            return res
        grid = self.roll()
        self.grid = grid
        res["grid"] = grid
        pm = self.payout_mult()
        cat = round(2 * g) if self.has("lucky_cat") else 0
        for key, s, cells in self.find(grid):
            coins = max(1, round(self.value(s) * self.mult(key) * g * pm * COIN)) + cat
            res["wins"].append({"key": key, "name": PATTERNS[key][0], "symbol": s, "cells": cells,
                                "mult": self.mult(key), "value": self.value(s), "coins": coins})
        total = sum(w["coins"] for w in res["wins"])
        if res["wins"]:
            if self.has("mirror"):
                best = max(w["coins"] for w in res["wins"])
                total += best
                res["extras"].append(("Hand Mirror", f"+{fmt(best)}"))
            if self.has("abacus") and len(res["wins"]) > 1:
                k = 1 + 0.5 * (len(res["wins"]) - 1)
                total = round(total * k)
                res["extras"].append(("Abacus", f"x{k:g}"))
            if self.has("wishing_well") and self.streak:
                k = 1 + 0.25 * self.streak
                total = round(total * k)
                res["extras"].append(("Wishing Well", f"x{k:g}"))
            if self.has("die") and rng.random() < 1 / 6:
                total *= 2
                res["extras"].append(("Loaded Die", "x2"))
            if self.has("clover_field") and any(w["symbol"] == "clover" for w in res["wins"]):
                self.tickets += 1
                res["tickets"] += 1
                res["extras"].append(("Clover Field", "+1 ticket"))
            self.streak = 0
        else:
            self.streak += 1
            if self.has("magnet"):
                m = round(3 * g)
                total += m
                res["extras"].append(("Coin Magnet", f"+{m}"))
        if lever:
            total += lever
            res["extras"].append(("Golden Lever", f"+{lever}"))
        res["total"] = total
        self.pocket += total
        self.total_won += total
        self.best_spin = max(self.best_spin, total)
        self._after_spin(res)
        return res

    def _after_spin(self, res):
        if self.spins > 0:
            return
        if self.round < ROUNDS:
            self.round += 1
            self.stage = "package"
            res["interest"] = self.start_round()
        else:
            res["deadline"] = self.deadline_end()

    # ---- the ATM ----
    def deposit(self, amount=None):
        """Put coins in the ATM (all of them, or this many). Returns what the bank gained."""
        amount = self.pocket if amount is None else max(0, min(self.pocket, amount))
        if amount <= 0 or self.stage in ("dead", "won"):
            return 0
        self.pocket -= amount
        if self.has("coin_purse"):
            amount = round(amount * 1.1)
        self.bank += amount
        return amount

    def spin_money(self):
        """What the next round's seven spins will cost (what to keep in your pocket)."""
        if self.stage == "spin" and self.round == ROUNDS:
            return 0
        return 7 * self.spin_price()

    def can_pay_early(self):
        return self.stage == "package" and self.bank >= self.debt

    def pay_early(self):
        if not self.can_pay_early():
            return None
        unused = ROUNDS - self.round + 1
        self.tickets += 2 * unused
        out = self.deadline_end()
        out["bonus"] = 2 * unused
        return out

    def deadline_end(self):
        """The ATM takes the debt (from your pocket too, if the bank is short)."""
        out = {"debt": self.debt}
        if self.bank < self.debt and self.bank + self.pocket >= self.debt:
            need = self.debt - self.bank
            self.pocket -= need
            self.bank += need
            out["topped"] = need
        if self.bank < self.debt:
            if self.has("rope_ladder"):
                self.charms.remove("rope_ladder")
                self.ladder_used = True
                out["ladder"] = True
                self.bank = 0
            else:
                self.stage = "dead"
                self.cause = "debt"
                out["dead"] = True
                return out
        else:
            self.bank -= self.debt
        self.stage = "phone"
        self.offers = self.call()
        out["paid"] = True
        return out

    # ---- the phone ----
    def call(self):
        rng = self.rng
        n = 4 if self.has("red_phone") else 3
        d = self.deadline
        kinds = ["normal"] * n
        if rng.random() < 0.35:
            kinds[rng.randrange(n)] = "evil"
        if rng.random() < 0.2:
            kinds[rng.randrange(n)] = "holy"
        out, seen = [], set()
        for kind in kinds:
            for _try in range(20):
                o = self._offer(kind, d)
                if o["id"] + o.get("arg", "") not in seen:
                    seen.add(o["id"] + o.get("arg", ""))
                    out.append(o)
                    break
        return out

    def _offer(self, kind, d):
        rng = self.rng
        if kind == "holy":
            return rng.choice([
                {"kind": kind, "id": "all_values", "name": "Blessing of Plenty", "desc": "Every symbol is worth +2."},
                {"kind": kind, "id": "less_six", "name": "Sanctuary", "desc": "666 is 1% less likely."},
                {"kind": kind, "id": "all_patterns", "name": "Halo", "desc": "Every pattern's multiplier +1."},
                {"kind": kind, "id": "gift", "name": "Alms", "desc": "+6 Clover Tickets and a fresh shelf of charms."}])
        if kind == "evil":
            sym = rng.choice(SYMBOLS)
            return rng.choice([
                {"kind": kind, "id": "double", "name": "Devil's Bargain",
                 "desc": "Everything pays x2 - but 666 is 2% more likely."},
                {"kind": kind, "id": "luck_debt", "name": "Borrowed Luck", "desc": "+6 Luck - but the next debt is 30% bigger."},
                {"kind": kind, "id": "tickets_interest", "name": "Pawned Savings",
                 "desc": "+10 Clover Tickets - but the ATM pays 2% less interest."},
                {"kind": kind, "id": "sacrifice", "arg": sym, "name": "Sacrifice",
                 "desc": f"{SYMBOL_NAME[sym]}s are worth +{4 + 2 * d} - but you lose your oldest charm."}])
        sym = rng.choice(SYMBOLS)
        pat = rng.choice(list(PATTERNS))
        step = {"h3": 1, "h4": 1, "h5": 2, "vertical": 1, "diagonal": 1, "zig": 2, "zag": 2}.get(pat, 3)
        n = 1 + d // 3
        options = [
            {"kind": kind, "id": "value", "arg": sym, "n": n, "name": f"{SYMBOL_NAME[sym]} Charm",
             "desc": f"{SYMBOL_NAME[sym]}s are worth +{n}."},
            {"kind": kind, "id": "weight", "arg": sym, "name": f"More {SYMBOL_NAME[sym]}s",
             "desc": f"{SYMBOL_NAME[sym]}s come up more often."},
            {"kind": kind, "id": "pattern", "arg": pat, "n": step, "name": f"{PATTERNS[pat][0]} Tutor",
             "desc": f"{PATTERNS[pat][0]} patterns: multiplier +{step}."},
            {"kind": kind, "id": "luck", "name": "Lucky Streak", "desc": "+2 Luck."},
            {"kind": kind, "id": "tickets", "name": "Ticket Roll", "desc": "+3 Clover Tickets."},
            {"kind": kind, "id": "interest", "name": "Better Rates", "desc": "The ATM pays +3% more interest."}]
        if self.slots < MAX_SLOTS:
            options.append({"kind": kind, "id": "slot", "name": "Bigger Pockets", "desc": "+1 charm slot."})
        return rng.choice(options)

    def answer(self, i):
        if self.stage != "phone" or not 0 <= i < len(self.offers):
            return False
        o = self.offers[i]
        k, arg = o["id"], o.get("arg")
        if k == "value":
            self.value_bonus[arg] += o["n"]
        elif k == "weight":
            self.weight_bonus[arg] += 6
        elif k == "pattern":
            self.pattern_bonus[arg] += o["n"]
        elif k == "luck":
            self.luck += 2
        elif k == "tickets":
            self.tickets += 3
        elif k == "interest":
            self.interest += 0.03
        elif k == "slot":
            self.slots += 1
        elif k == "all_values":
            for s in SYMBOLS:
                self.value_bonus[s] += 2
        elif k == "less_six":
            self.risk -= 0.01
        elif k == "all_patterns":
            for p in PATTERNS:
                self.pattern_bonus[p] += 1
        elif k == "gift":
            self.tickets += 6
            self.restock()
        elif k == "double":
            self.pay_mult *= 2
            self.risk += 0.02
        elif k == "luck_debt":
            self.luck += 6
            self.debt_extra += 0.3
        elif k == "tickets_interest":
            self.tickets += 10
            self.interest = max(0.0, self.interest - 0.02)
        elif k == "sacrifice":
            self.value_bonus[arg] += 4 + 2 * self.deadline
            if self.charms:
                self.charms.pop(0)
        self.abilities.append((o["kind"], o["name"]))
        self.offers = []
        self.next_deadline()
        return True

    def hang_up(self):
        if self.stage == "phone":
            self.offers = []
            self.next_deadline()

    def next_deadline(self):
        self.deadline += 1
        if self.deadline > FINAL and not self.endless:
            self.won = True
            self.stage = "won"
            return
        self.debt = round(debt_for(self.deadline) * (1 + self.debt_extra))
        self.debt_extra = 0.0
        self.round = 1
        self.reroll_cost = 1
        self.restock()
        self.stage = "package"
        self.start_round()

    def keep_going(self):
        """Stay in the pit after climbing out: the deadlines go on."""
        if self.stage == "won":
            self.endless = True
            self.deadline -= 1
            self.next_deadline()

    # ---- the charm machine ----
    def restock(self):
        pool = [k for k in CHARMS if k not in self.charms]
        self.rng.shuffle(pool)
        self.store = pool[:4]

    def buy(self, i):
        if not 0 <= i < len(self.store) or self.store[i] is None or self.stage in ("dead", "won"):
            return "nothing"
        key = self.store[i]
        price = CHARMS[key][1]
        if price > self.tickets:
            return "tickets"
        if len(self.charms) >= self.slots:
            return "full"
        self.tickets -= price
        self.charms.append(key)
        self.store[i] = None
        return "ok"

    def sell(self, i):
        if not 0 <= i < len(self.charms) or self.stage in ("dead", "won"):
            return 0
        key = self.charms.pop(i)
        back = CHARMS[key][1] // 2
        self.tickets += back
        return back

    def reroll(self):
        if self.tickets < self.reroll_cost or self.stage in ("dead", "won"):
            return False
        self.tickets -= self.reroll_cost
        self.reroll_cost += 1
        self.restock()
        return True

    # ---- saving ----
    FIELDS = ("seed", "deadline", "round", "debt", "debt_extra", "bank", "pocket", "tickets", "spins", "stage",
              "luck", "charms", "slots", "value_bonus", "weight_bonus", "pattern_bonus", "pay_mult", "interest",
              "risk", "store", "reroll_cost", "offers", "abilities", "grid", "streak", "ladder_used", "won",
              "endless", "cause", "best_spin", "total_won", "spins_pulled", "sixes")

    def to_json(self):
        d = {k: getattr(self, k) for k in self.FIELDS}
        st = self.rng.getstate()
        d["rng"] = [st[0], list(st[1]), st[2]]
        return d

    @classmethod
    def from_json(cls, d):
        run = cls(d["seed"])
        for k in cls.FIELDS:
            if k in d:
                setattr(run, k, d[k])
        run.abilities = [tuple(a) for a in run.abilities]
        st = d.get("rng")
        if st:
            run.rng.setstate((st[0], tuple(st[1]), st[2]))
        return run
