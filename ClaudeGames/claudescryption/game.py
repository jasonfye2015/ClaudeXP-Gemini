"""Claudescryption's cards and battles: the rules of Leshy's game.

A battle is four lanes. Your creatures sit in the bottom row; Leshy's in the row above, with the cards he means to
play next waiting behind them. Each turn you draw (your deck or a squirrel), play cards - blood costs are paid by
sacrificing your own creatures, bone costs from the bones your dead leave behind - and ring the bell: your creatures
strike, lane by lane, then his do. Damage that reaches a player tips the scale; tip it five teeth your way to win.

Combat runs as a generator: the screen steps through it, one strike at a time."""
import random

# name -> (emoji, blood, bones, power, health, sigils, rarity)   rarity: c common, r rare, t terrain, s special
CARDS = {
    "Squirrel": ("🐿️", 0, 0, 0, 1, [], "s"),
    "Stoat": ("🦡", 1, 0, 1, 3, [], "c"),
    "Bullfrog": ("🐸", 1, 0, 1, 2, ["Mighty Leap"], "c"),
    "Wolf": ("🐺", 2, 0, 3, 2, [], "c"),
    "Wolf Cub": ("🐕", 1, 0, 1, 1, ["Fledgling"], "c"),
    "Raven": ("🐦‍⬛", 2, 0, 2, 3, ["Airborne"], "c"),
    "Sparrow": ("🐦", 1, 0, 1, 2, ["Airborne"], "c"),
    "Mantis": ("🦗", 1, 0, 1, 1, ["Bifurcated Strike"], "c"),
    "Mantis God": ("🙏", 1, 0, 0, 1, ["Trifurcated Strike"], "r"),
    "Adder": ("🐍", 2, 0, 1, 1, ["Touch of Death"], "c"),
    "Black Goat": ("🐐", 1, 0, 0, 1, ["Worthy Sacrifice"], "r"),
    "Cat": ("🐈", 1, 0, 0, 1, ["Many Lives"], "r"),
    "Grizzly": ("🐻", 3, 0, 4, 6, [], "c"),
    "Moose Buck": ("🫎", 3, 0, 3, 7, ["Sprinter"], "r"),
    "Elk": ("🦌", 2, 0, 2, 4, ["Sprinter"], "c"),
    "Elk Fawn": ("🦌", 1, 0, 1, 1, ["Sprinter", "Fledgling"], "c"),
    "Field Mice": ("🐁", 2, 0, 2, 2, ["Fecundity"], "c"),
    "Warren": ("🕳️", 1, 0, 0, 2, ["Rabbit Hole"], "c"),
    "Rabbit": ("🐇", 0, 0, 0, 1, [], "s"),
    "Beehive": ("🍯", 1, 0, 0, 2, ["Bees Within"], "c"),
    "Bee": ("🐝", 0, 0, 1, 1, ["Airborne"], "s"),
    "Porcupine": ("🦔", 1, 0, 1, 2, ["Sharp Quills"], "c"),
    "Skunk": ("🦨", 1, 0, 0, 3, ["Stinky"], "c"),
    "Mole": ("🐀", 1, 0, 0, 4, ["Burrower"], "c"),
    "Bloodhound": ("🐕‍🦺", 2, 0, 2, 3, ["Guardian"], "c"),
    "Kingfisher": ("🐟", 1, 0, 1, 1, ["Airborne", "Waterborne"], "c"),
    "River Snapper": ("🐢", 2, 0, 1, 6, [], "c"),
    "Coyote": ("🐾", 0, 4, 2, 1, [], "c"),
    "Opossum": ("🐭", 0, 2, 1, 1, [], "c"),
    "Vulture": ("🦅", 0, 8, 3, 3, ["Airborne"], "r"),
    "Rattler": ("🪱", 0, 6, 3, 1, [], "c"),
    "Alpha": ("🐺", 0, 4, 1, 2, ["Leader"], "c"),
    "Corpse Maggots": ("🐛", 0, 5, 1, 2, ["Corpse Eater"], "c"),
    "Beaver": ("🦫", 2, 0, 1, 3, ["Dam Builder"], "c"),
    "Ouroboros": ("🐉", 2, 0, 1, 1, ["Unkillable"], "r"),
    "Amalgam": ("🧬", 2, 0, 3, 3, [], "r"),
    "Pack Mule": ("🫏", 0, 0, 0, 5, ["Sprinter"], "s"),
    "Dam": ("🪵", 0, 0, 0, 2, [], "t"),
    "Boulder": ("🪨", 0, 0, 0, 5, [], "t"),
    "Grand Fir": ("🌲", 0, 0, 0, 3, ["Mighty Leap"], "t"),
    "Gold Nugget": ("🪙", 0, 0, 0, 2, [], "t"),
    "Steel Trap": ("🪤", 0, 0, 0, 1, ["Steel Trap"], "t"),
    "Bait Bucket": ("🪣", 0, 0, 0, 1, [], "t"),
    "The Moon": ("🌕", 0, 0, 1, 24, ["Mighty Leap", "All Lanes"], "s"),
}
SIGILS = {
    "Airborne": ("🪶", "Attacks the opponent directly, flying over creatures."),
    "Mighty Leap": ("🦘", "Blocks Airborne attacks."),
    "Touch of Death": ("☠️", "Kills any creature it damages."),
    "Bifurcated Strike": ("✌️", "Strikes the lanes to its left and right."),
    "Trifurcated Strike": ("🔱", "Strikes the lanes to its left, ahead and right."),
    "Sprinter": ("💨", "Moves a lane at the end of its owner's turn."),
    "Fecundity": ("🥚", "When played, a copy goes into your hand."),
    "Unkillable": ("♾️", "When it dies, it returns to your hand."),
    "Worthy Sacrifice": ("🩸", "Counts as three blood when sacrificed."),
    "Many Lives": ("🐾", "Survives being sacrificed."),
    "Bone King": ("👑", "Gives four bones when it dies."),
    "Stinky": ("🤢", "The creature opposite it loses 1 power."),
    "Rabbit Hole": ("🕳️", "When played, a Rabbit goes into your hand."),
    "Bees Within": ("🐝", "When struck, a Bee goes into your hand."),
    "Sharp Quills": ("🌵", "Whatever strikes it takes 1 damage."),
    "Guardian": ("🛡️", "Moves to block a creature played opposite an empty lane."),
    "Burrower": ("⛏️", "Moves to block attacks on empty lanes."),
    "Leader": ("🚩", "Creatures beside it gain 1 power."),
    "Waterborne": ("🌊", "Submerged: attacks pass over it."),
    "Corpse Eater": ("🪱", "From your hand, takes the place of a creature of yours that dies."),
    "Dam Builder": ("🪵", "When played, builds Dams in the lanes beside it."),
    "Fledgling": ("🐣", "Grows up after a turn."),
    "Steel Trap": ("🪤", "When it dies, kills the creature opposite."),
    "All Lanes": ("🌕", "Fills every lane; strikes them all."),
}
GROWS = {"Wolf Cub": "Wolf", "Elk Fawn": "Elk"}
REGIONS = [
    {"name": "The Woodlands", "boss": "The Prospector", "colour": "#2E3B22",
     "pool": ["Stoat", "Bullfrog", "Opossum", "Skunk", "Wolf Cub", "Sparrow", "Mantis", "Elk Fawn", "Coyote",
              "Alpha", "Raven", "Wolf"], "terrain": ["Boulder", "Grand Fir"]},
    {"name": "The Wetlands", "boss": "The Angler", "colour": "#1F3A3A",
     "pool": ["Bullfrog", "Kingfisher", "Skunk", "Beehive", "Sparrow", "Beaver", "River Snapper", "Adder",
              "Corpse Maggots", "Field Mice", "Rattler", "Raven"], "terrain": ["Boulder", "Bait Bucket"]},
    {"name": "The Snow Line", "boss": "The Trapper", "colour": "#2C3440",
     "pool": ["Stoat", "Opossum", "Porcupine", "Elk Fawn", "Mole", "Bloodhound", "Field Mice", "Raven", "Elk",
              "Adder", "Wolf", "Alpha", "Vulture", "Grizzly", "Moose Buck"], "terrain": ["Grand Fir", "Boulder", "Steel Trap"]},
]
BOSS_POOL = {"The Prospector": ["Stoat", "Pack Mule", "Coyote", "Bloodhound", "Wolf", "Alpha"],     # (weak to strong)
             "The Angler": ["Bullfrog", "Bait Bucket", "Kingfisher", "Beehive", "River Snapper", "Adder"],
             "The Trapper": ["Porcupine", "Bloodhound", "Raven", "Elk", "Wolf", "Grizzly"],
             "Leshy": ["Porcupine", "Bloodhound", "Raven", "Adder", "Wolf", "Vulture", "Grizzly", "Moose Buck"]}
REWARDS = [n for n, c in CARDS.items() if c[6] in "c"]
RARES = [n for n, c in CARDS.items() if c[6] == "r"]


def spec(name, **kw):
    """A card in a deck: what it is, and what's been done to it (campfire, stones, fusing)."""
    d = {"name": name, "power": 0, "health": 0, "sigils": [], "custom": None}
    d.update(kw)
    return d


def info(s):
    """(emoji, blood, bones, power, health, sigils) of a deck card, with its changes."""
    if s.get("custom"):
        c = s["custom"]
        base = (c["emoji"], c["blood"], c["bones"], c["power"], c["health"], list(c["sigils"]))
    else:
        e, b, x, pw, hp, sg, _r = CARDS[s["name"]]
        base = (e, b, x, pw, hp, list(sg))
    sig = base[5] + [g for g in s.get("sigils", []) if g not in base[5]]
    return base[0], base[1], base[2], base[3] + s.get("power", 0), base[4] + s.get("health", 0), sig


class Creature:
    def __init__(self, s, owner):
        self.spec = s
        self.owner = owner                       # "you" or "leshy"
        e, self.blood, self.bones, self.base_power, self.max_health, self.sigils = info(s)
        self.emoji = e
        self.name = s["custom"]["name"] if s.get("custom") else s["name"]
        self.health = self.max_health
        self.turns = 0
        self.direction = 1                       # sprinters
        self.gold = False

    def has(self, sigil):
        return sigil in self.sigils


class Battle:
    """One battle. `you` and `leshy` are the two front rows; `queue` is Leshy's back row."""

    def __init__(self, deck, region, difficulty, boss=None, deathcards=(), seed=None):
        self.rng = random.Random(seed)
        self.region = region
        self.difficulty = difficulty
        self.boss = boss
        self.phase = 1
        self.you = [None] * 4
        self.leshy = [None] * 4
        self.queue = [None] * 4
        self.deck = [dict(s) for s in deck]
        self.rng.shuffle(self.deck)
        self.squirrels = 20
        self.hand = []
        self.bones = 0
        self.scale = 0                           # + toward Leshy (you're winning), - toward you
        self.turn = 0
        self.drawn = True                        # the first turn starts with a hand, no draw
        self.over = None                         # "won" / "lost" / "phase"
        self.log = []
        self.deathcards = list(deathcards)
        self.tricks = 0                          # boss tricks used this phase
        self.rising = False                      # the Moon's first turn: it rises, it doesn't strike
        self.hand.append(spec("Squirrel"))
        for _ in range(3):
            self.draw_deck()
        self.plan = self._make_plan()
        self._leshy_turn_plays(0)
        if boss is None and self.rng.random() < 0.35:      # a little terrain on his side
            lane = self.rng.randrange(4)
            self.leshy[lane] = Creature(spec(self.rng.choice(REGIONS[region]["terrain"])), "leshy")

    def say(self, text):
        self.log.append(text)
        del self.log[:-6]

    # ---- Leshy's plan ----
    def _make_plan(self):
        """What he'll play, turn by turn: harder as the region and the map go on."""
        reg = REGIONS[self.region]
        pool = list(BOSS_POOL.get(self.boss) or reg["pool"])
        plan = []
        strength = 1 + self.difficulty
        reach = min(len(pool), int(2 + strength * 2))   # (early battles draw only from the weak end)
        counts = {1: (0, 1, 1), 2: (0, 1, 1, 1, 2), 3: (1, 1, 1, 2)}.get(round(strength), (1, 1, 2, 2))
        for t in range(40):
            k = 1 if t < 2 else self.rng.choice(counts)
            turn = []
            for _ in range(k):
                if self.boss == "Leshy" and self.deathcards and self.rng.random() < 0.35:
                    turn.append(self.rng.choice(self.deathcards))
                else:
                    ramp = 1 + t // 2 if self.boss else 2 + t        # (stronger cards as turns pass)
                    turn.append(spec(self.rng.choice(pool[:min(reach, ramp)])))
            plan.append(turn)
        return plan

    def _leshy_turn_plays(self, t):
        for s in (self.plan[t] if t < len(self.plan) else []):
            free = [i for i in range(4) if self.queue[i] is None]
            if not free:
                break
            lane = self.rng.choice(free)
            self.queue[lane] = Creature(s if isinstance(s, dict) else spec(s), "leshy")

    # ---- drawing and playing ----
    def draw_deck(self):
        if self.deck:
            self.hand.append(self.deck.pop())
            return True
        return False

    def draw(self, pile):
        if self.drawn or self.over:
            return False
        if pile == "deck" and self.deck:
            self.draw_deck()
        elif pile == "squirrel" and self.squirrels > 0:
            self.squirrels -= 1
            self.hand.append(spec("Squirrel"))
        elif not self.deck and self.squirrels <= 0:
            pass                                    # (nothing left to draw)
        else:
            return False
        self.drawn = True
        return True

    def can_draw(self):
        return not self.drawn and (self.deck or self.squirrels > 0)

    def blood_of(self, lanes):
        return sum(3 if self.you[i].has("Worthy Sacrifice") else 1 for i in lanes if self.you[i])

    def can_afford(self, card):
        _e, blood, bones, *_ = info(card)
        if bones and self.bones < bones:
            return False
        if blood:
            return self.blood_of([i for i in range(4) if self.you[i]]) >= blood
        return True

    def play(self, hand_index, lane, sacrifices=()):
        """Play a card from the hand into an empty lane (after any sacrifices). Returns False if it can't."""
        card = self.hand[hand_index]
        _e, blood, bones, *_ = info(card)
        if bones > self.bones or self.blood_of(sacrifices) < blood:
            return False
        for i in sacrifices:
            c = self.you[i]
            if c is None:
                continue
            if c.has("Many Lives"):
                continue
            self.you[i] = None
            self._died(c, i, "you", sacrificed=True)
        if self.you[lane] is not None:
            return False
        self.bones -= bones
        self.hand.pop(hand_index)
        c = Creature(card, "you")
        self.you[lane] = c
        self._on_play(c, lane, "you")
        return True

    def _on_play(self, c, lane, side):
        row = self.you if side == "you" else self.leshy
        if c.has("Fecundity") and side == "you":
            self.hand.append(dict(c.spec))
        if c.has("Rabbit Hole") and side == "you":
            self.hand.append(spec("Rabbit"))
        if c.has("Dam Builder"):
            for j in (lane - 1, lane + 1):
                if 0 <= j < 4 and row[j] is None:
                    row[j] = Creature(spec("Dam"), side)
        other = self.leshy if side == "you" else self.you
        if other[lane] is None:                    # a Guardian on the other side moves to block it
            for j in range(4):
                g = other[j]
                if g and g.has("Guardian") and other[lane] is None:
                    other[lane], other[j] = g, None
                    break

    # ---- deaths ----
    def _died(self, c, lane, side, sacrificed=False):
        if side == "you":
            self.bones += 4 if c.has("Bone King") else 1
            if c.has("Unkillable") and c.name not in ("Squirrel",):
                s = dict(c.spec)
                if c.name == "Ouroboros":
                    s["power"] = s.get("power", 0) + 1
                    s["health"] = s.get("health", 0) + 1
                self.hand.append(s)
            if not sacrificed:                      # Corpse Eaters in your hand take its place
                for k, h in enumerate(self.hand):
                    if "Corpse Eater" in info(h)[5] and self.you[lane] is None:
                        self.hand.pop(k)
                        self.you[lane] = Creature(h, "you")
                        self.say("Corpse Maggots crawl into the empty place.")
                        break
        if c.has("Steel Trap"):                    # the trap springs on whatever's opposite
            other = self.you if side == "leshy" else self.leshy
            if other[lane] is not None:
                victim = other[lane]
                other[lane] = None
                self._died(victim, lane, "you" if side == "leshy" else "leshy")
                self.say("The steel trap snaps shut.")

    def _kill(self, side, lane):
        row = self.you if side == "you" else self.leshy
        c = row[lane]
        if c is None:
            return
        row[lane] = None
        self._died(c, lane, side)

    # ---- combat ----
    def power_of(self, side, lane):
        row = self.you if side == "you" else self.leshy
        other = self.leshy if side == "you" else self.you
        c = row[lane]
        if c is None:
            return 0
        p = c.base_power
        for j in (lane - 1, lane + 1):
            if 0 <= j < 4 and row[j] is not None and row[j].has("Leader"):
                p += 1
        if other[lane] is not None and other[lane].has("Stinky"):
            p -= 1
        return max(0, p)

    def _strike(self, side, lane):
        """One creature's attack: yields after each hit so it can be shown."""
        row = self.you if side == "you" else self.leshy
        other = self.leshy if side == "you" else self.you
        c = row[lane]
        if c is None:
            return
        lanes = [lane]
        if c.has("All Lanes"):
            lanes = [0, 1, 2, 3]
        elif c.has("Trifurcated Strike"):
            lanes = [lane - 1, lane, lane + 1]
        elif c.has("Bifurcated Strike"):
            lanes = [lane - 1, lane + 1]
        for t in lanes:
            if not 0 <= t < 4 or row[lane] is not c:
                continue
            power = self.power_of(side, lane)
            if power <= 0:
                continue
            target = other[t]
            if target is None:                     # an empty lane: a Burrower may dig in to block
                for j in range(4):
                    b = other[j]
                    if b and b.has("Burrower") and other[t] is None:
                        other[t], other[j] = b, None
                        target = b
                        break
            flying = c.has("Airborne") and not (target and target.has("Mighty Leap"))
            if target is None or flying or target.has("Waterborne"):
                self.scale += power if side == "you" else -power
                yield ("face", side, lane, t, power)
                if abs(self.scale) >= 5 and not self.boss_moon_guard():
                    return
                continue
            target.health -= power
            yield ("hit", side, lane, t, power)
            if target.has("Sharp Quills"):
                c.health -= 1
            if target.has("Bees Within") and target.owner == "you":
                self.hand.append(spec("Bee"))
            if target.health <= 0 or (c.has("Touch of Death") and not target.name == "The Moon"):
                for j in range(4):
                    if other[j] is target:
                        self._kill("leshy" if side == "you" else "you", j)
            if c.health <= 0:
                self._kill(side, lane)
                return

    def boss_moon_guard(self):
        return any(c is not None and c.name == "The Moon" for c in self.leshy)

    def ring_bell(self):
        """Your attack, then his turn: a generator of things that happen."""
        if self.over:
            return
        for lane in range(4):
            yield from self._strike("you", lane)
            if self._check():
                return
        self._end_of_turn("you")
        yield ("leshy_turn",)
        # his turn: the queue steps forward, he plays more, a boss may try a trick, then he strikes
        for lane in range(4):
            if self.queue[lane] is not None and self.leshy[lane] is None:
                self.leshy[lane], self.queue[lane] = self.queue[lane], None
                self._on_play(self.leshy[lane], lane, "leshy")
                yield ("advance", lane)
        self.turn += 1
        self._leshy_turn_plays(self.turn)
        yield from self._boss_trick()
        if self.turn >= 30:                         # (a battle can't go on for ever: the cold creeps in)
            self.scale -= 1
            self.say("The cold creeps in. Leshy grows impatient.")
            yield ("face", "leshy", 0, 0, 1)
            if self._check():
                return
        for lane in range(4):
            if self.rising:
                self.rising = False
                self.say("The Moon hangs in the sky, gathering itself.")
                break
            yield from self._strike("leshy", lane)
            if self._check():
                return
            if self.leshy[lane] is not None and self.leshy[lane].has("All Lanes"):
                break
        self._end_of_turn("leshy")
        for row in (self.you, self.leshy):         # fledglings grow
            for i, c in enumerate(row):
                if c is not None:
                    c.turns += 1
                    if c.has("Fledgling") and c.turns >= 1 and c.name in GROWS:
                        grown = Creature(spec(GROWS[c.name], power=c.spec.get("power", 0),
                                              health=c.spec.get("health", 0)), c.owner)
                        row[i] = grown
        self.drawn = not (self.deck or self.squirrels > 0)
        yield ("your_turn",)

    def _end_of_turn(self, side):
        row = self.you if side == "you" else self.leshy
        moved = set()
        for i in range(4):
            c = row[i]
            if c is None or id(c) in moved or not c.has("Sprinter"):
                continue
            j = i + c.direction
            if not 0 <= j < 4 or row[j] is not None:
                c.direction = -c.direction
                j = i + c.direction
            if 0 <= j < 4 and row[j] is None:
                row[j], row[i] = c, None
                moved.add(id(c))

    def _check(self):
        moon = self.boss_moon_guard()
        if self.boss == "Leshy" and self.phase == 2 and not moon:      # the Moon is destroyed
            self.over = "won"
            return True
        if self.scale >= 5 and not moon:
            self.over = "phase" if self.boss and self.phase == 1 else "won"
            return True
        if self.scale <= -5:
            self.over = "lost"
            return True
        return False

    # ---- bosses ----
    def _boss_trick(self):
        b = self.boss
        if not b or self.tricks >= (1 if self.phase == 1 else 2) or self.turn < 4 + self.tricks * 3:
            return
        mine = [i for i in range(4) if self.you[i] is not None and self.you[i].name not in ("Gold Nugget",)]
        if b == "The Prospector" and mine:
            self.tricks += 1
            for i in sorted(mine, key=lambda k: -self.power_of("you", k))[:1]:      # (your strongest)
                self.you[i] = Creature(spec("Gold Nugget"), "you")
            self.say("\"GOLD!\" The Prospector's pickaxe turns your creatures to gold.")
            yield ("trick", b)
        elif b == "The Angler" and mine:
            i = max(mine, key=lambda k: self.power_of("you", k))
            if self.leshy[i] is None:
                self.tricks += 1
                self.leshy[i], self.you[i] = self.you[i], None
                self.leshy[i].owner = "leshy"
                self.say("The Angler's hook drags your creature to his side.")
                yield ("trick", b)
        elif b == "The Trapper":
            free = [i for i in range(4) if self.leshy[i] is None]
            if free:
                self.tricks += 1
                for i in free[:1]:
                    self.leshy[i] = Creature(spec("Steel Trap"), "leshy")
                self.say("The Trapper sets his steel traps.")
                yield ("trick", b)
        elif b == "Leshy" and self.phase == 1 and mine and self.turn >= 6:
            self.tricks += 1
            i = self.rng.choice(mine)
            self.you[i] = Creature(spec("Gold Nugget"), "you")
            self.say("Leshy wears the Prospector's mask for a moment. \"Gold.\"")
            yield ("trick", b)

    def next_phase(self):
        """A boss's second phase: the scale resets and the board is cleared on his side."""
        self.phase = 2
        self.scale = 0
        self.tricks = 0
        self.over = None
        self.leshy = [None] * 4
        self.queue = [None] * 4
        self.plan = self._make_plan()
        if self.boss == "Leshy":
            moon = Creature(spec("The Moon"), "leshy")
            self.leshy = [moon] * 4
            self.rising = True
            self.plan = []                       # (the Moon fills every lane; nothing else comes)
            self.hand += [spec("Squirrel"), spec("Squirrel")]
            self.say("\"Behold... the Moon.\" Two squirrels scurry to your side.")
        else:
            self.plan = self._make_plan()
            self._leshy_turn_plays(self.turn)
            self.say(f"{self.boss} takes off his mask... no. He puts on another.")
