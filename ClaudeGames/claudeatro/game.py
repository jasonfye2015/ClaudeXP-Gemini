"""Claudeatro's rules: poker hands, chips x mult, jokers, tarots and planets, the shop, the blinds and the antes.

No Qt in here. A run is plain data (cards, jokers and consumables are dicts), so it saves as JSON; the window just
shows it and calls play(), discard(), buy() and the rest."""
import random

SUITS = "SHDC"
SUIT_SYMBOL = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
SUIT_NAME = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
FACE = (11, 12, 13)


def rank_label(r):
    return {11: "J", 12: "Q", 13: "K", 14: "A"}.get(r, str(r))


def rank_name(r):
    return {11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}.get(r, str(r))


def rank_chips(r):
    return 11 if r == 14 else min(10, r)


def fmt(n):
    n = int(n)
    return f"{n:.3e}".replace("e+", "e") if abs(n) >= 10 ** 11 else f"{n:,}"


# name: base chips, base mult, chips per level, mult per level (best first)
HANDS = [("Flush Five", 160, 16, 50, 3), ("Flush House", 140, 14, 40, 4), ("Five of a Kind", 120, 12, 35, 3),
         ("Straight Flush", 100, 8, 40, 4), ("Four of a Kind", 60, 7, 30, 3), ("Full House", 40, 4, 25, 2),
         ("Flush", 35, 4, 15, 2), ("Straight", 30, 4, 30, 3), ("Three of a Kind", 30, 3, 20, 2),
         ("Two Pair", 20, 2, 20, 1), ("Pair", 10, 2, 15, 1), ("High Card", 5, 1, 10, 1)]
HAND_INFO = {h[0]: h[1:] for h in HANDS}
SECRET = ("Flush Five", "Flush House", "Five of a Kind")      # (hidden until you've played one)

PLANETS = {"Pluto": "High Card", "Mercury": "Pair", "Uranus": "Two Pair", "Venus": "Three of a Kind",
           "Saturn": "Straight", "Jupiter": "Flush", "Earth": "Full House", "Mars": "Four of a Kind",
           "Neptune": "Straight Flush", "Planet X": "Five of a Kind", "Ceres": "Flush House", "Eris": "Flush Five"}

ENHANCEMENTS = {"bonus": ("Bonus Card", "+30 extra Chips"),
                "mult": ("Mult Card", "+4 Mult"),
                "wild": ("Wild Card", "Counts as every suit"),
                "glass": ("Glass Card", "x2 Mult; 1 in 4 chance to break when scored"),
                "steel": ("Steel Card", "x1.5 Mult while this card stays in hand"),
                "stone": ("Stone Card", "+50 Chips; no rank or suit; always scores"),
                "gold": ("Gold Card", "$3 if this card is held in hand at the end of the round"),
                "lucky": ("Lucky Card", "1 in 5 chance for +20 Mult; 1 in 15 chance to win $20")}
EDITIONS = {"foil": ("Foil", "+50 Chips"), "holo": ("Holographic", "+10 Mult"), "poly": ("Polychrome", "x1.5 Mult")}
EDITION_COST = {"foil": 2, "holo": 3, "poly": 5}

# name: (emoji, rarity 1 common / 2 uncommon / 3 rare, cost, what it does)
JOKERS = {
    "Joker": ("🃏", 1, 2, "+4 Mult"),
    "Greedy Joker": ("💎", 1, 5, "Played ♦ Diamonds give +3 Mult when scored"),
    "Lusty Joker": ("💋", 1, 5, "Played ♥ Hearts give +3 Mult when scored"),
    "Wrathful Joker": ("😤", 1, 5, "Played ♠ Spades give +3 Mult when scored"),
    "Gluttonous Joker": ("🍗", 1, 5, "Played ♣ Clubs give +3 Mult when scored"),
    "Jolly Joker": ("😀", 1, 3, "+8 Mult if the played hand contains a Pair"),
    "Zany Joker": ("🤪", 1, 4, "+12 Mult if the played hand contains a Three of a Kind"),
    "Mad Joker": ("😠", 1, 4, "+10 Mult if the played hand contains a Two Pair"),
    "Crazy Joker": ("🌀", 1, 4, "+12 Mult if the played hand contains a Straight"),
    "Droll Joker": ("😏", 1, 4, "+10 Mult if the played hand contains a Flush"),
    "Sly Joker": ("🦊", 1, 3, "+50 Chips if the played hand contains a Pair"),
    "Wily Joker": ("🐺", 1, 4, "+100 Chips if the played hand contains a Three of a Kind"),
    "Clever Joker": ("🦉", 1, 4, "+80 Chips if the played hand contains a Two Pair"),
    "Devious Joker": ("🐍", 1, 4, "+100 Chips if the played hand contains a Straight"),
    "Crafty Joker": ("🧶", 1, 4, "+80 Chips if the played hand contains a Flush"),
    "Half Joker": ("🌗", 1, 5, "+20 Mult if the played hand has 3 or fewer cards"),
    "Banner": ("🚩", 1, 5, "+30 Chips for each remaining discard"),
    "Mystic Summit": ("🏔️", 1, 5, "+15 Mult when 0 discards remain"),
    "Misprint": ("🖨️", 1, 4, "+0 to +23 Mult"),
    "Raised Fist": ("✊", 1, 5, "Adds double the rank of the lowest card held in hand to Mult"),
    "Scary Face": ("👹", 1, 4, "Played face cards give +30 Chips when scored"),
    "Smiley Face": ("😊", 1, 4, "Played face cards give +5 Mult when scored"),
    "Abstract Joker": ("🎨", 1, 4, "+3 Mult for each Joker you have"),
    "Gros Michel": ("🍌", 1, 5, "+15 Mult; 1 in 6 chance it's destroyed at the end of the round"),
    "Even Steven": ("👬", 1, 4, "Played 10s, 8s, 6s, 4s and 2s give +4 Mult when scored"),
    "Odd Todd": ("🎲", 1, 4, "Played Aces, 9s, 7s, 5s and 3s give +31 Chips when scored"),
    "Scholar": ("🎓", 1, 4, "Played Aces give +20 Chips and +4 Mult when scored"),
    "Business Card": ("💼", 1, 4, "Played face cards have a 1 in 2 chance to give $2 when scored"),
    "Supernova": ("💥", 1, 5, "Adds the number of times this poker hand has been played this run to Mult"),
    "Ride the Bus": ("🚌", 1, 6, "Gains +1 Mult per hand played in a row without a scoring face card"),
    "Blue Joker": ("🔵", 1, 5, "+2 Chips for each card remaining in your deck"),
    "Green Joker": ("🟢", 1, 4, "Gains +1 Mult per hand played; loses 1 Mult per discard"),
    "Ice Cream": ("🍦", 1, 5, "+100 Chips; -5 Chips for every hand played"),
    "Popcorn": ("🍿", 1, 5, "+20 Mult; -4 Mult for every round played"),
    "Walkie Talkie": ("📻", 1, 4, "Played 10s and 4s give +10 Chips and +4 Mult when scored"),
    "Golden Joker": ("🪙", 1, 6, "Earn $4 at the end of the round"),
    "Egg": ("🥚", 1, 4, "Gains $3 of sell value at the end of every round"),
    "Delayed Gratification": ("⏳", 1, 4, "Earn $2 per discard left if no discards were used this round"),
    "Juggler": ("🤹", 1, 4, "+1 hand size"),
    "Drunkard": ("🍺", 1, 4, "+1 discard every round"),
    "Credit Card": ("💳", 1, 1, "You can go up to $20 into debt"),
    "Chaos the Clown": ("🤡", 1, 4, "1 free reroll in every shop"),
    "Hanging Chad": ("🗳️", 1, 4, "Retrigger the first played card used in scoring"),
    "Photograph": ("📷", 1, 5, "The first played face card gives x2 Mult when scored"),
    "Square Joker": ("🟥", 1, 4, "Gains +4 Chips whenever the played hand has exactly 4 cards"),
    "Runner": ("🏃", 1, 5, "Gains +15 Chips whenever the played hand contains a Straight"),
    "Splash": ("💦", 1, 3, "Every played card counts in scoring"),
    "Cavendish": ("🍌", 1, 4, "x3 Mult; 1 in 1000 chance it's destroyed at the end of the round"),
    "Hiker": ("🥾", 2, 5, "Every played card permanently gains +5 Chips when scored"),
    "Fibonacci": ("🐚", 2, 8, "Played Aces, 2s, 3s, 5s and 8s give +8 Mult when scored"),
    "Four Fingers": ("✋", 2, 7, "Flushes and Straights can be made with 4 cards"),
    "Shortcut": ("↗️", 2, 7, "Straights can skip a rank (like 10 8 6 5 3)"),
    "Pareidolia": ("👁️", 2, 5, "Every card counts as a face card"),
    "Smeared Joker": ("🖌️", 2, 7, "♥ Hearts and ♦ Diamonds count as one suit, and so do ♠ Spades and ♣ Clubs"),
    "Mime": ("🎭", 2, 5, "Retrigger the abilities of every card held in hand"),
    "Steel Joker": ("🔩", 2, 7, "x0.2 Mult for each Steel Card in your full deck"),
    "Constellation": ("✨", 2, 6, "Gains x0.1 Mult every time a Planet card is used"),
    "Hack": ("💻", 2, 6, "Retrigger every played 2, 3, 4 and 5"),
    "Dusk": ("🌆", 2, 5, "Retrigger every played card in the final hand of the round"),
    "Sock and Buskin": ("🩰", 2, 6, "Retrigger every played face card"),
    "Bootstraps": ("👢", 2, 7, "+2 Mult for every $5 you have"),
    "Blackboard": ("⬛", 2, 6, "x3 Mult if every card held in hand is a ♠ Spade or ♣ Club"),
    "Acrobat": ("🤸", 2, 6, "x3 Mult on the final hand of the round"),
    "Joker Stencil": ("🖼️", 2, 8, "x1 Mult for each empty Joker slot (Joker Stencil counts as empty)"),
    "Rocket": ("🚀", 2, 6, "Earn $1 at the end of the round; the payout grows by $2 for each Boss Blind beaten"),
    "To the Moon": ("📈", 2, 5, "Earn an extra $1 of interest for every $5 you have at the end of the round"),
    "Burglar": ("🦹", 2, 6, "When a Blind is selected, gain +3 hands and lose all discards"),
    "Shoot the Moon": ("🌕", 2, 5, "Every Queen held in hand gives +13 Mult"),
    "Cloud 9": ("☁️", 2, 7, "Earn $1 for each 9 in your full deck at the end of the round"),
    "Rough Gem": ("💠", 2, 7, "Played ♦ Diamonds earn $1 when scored"),
    "Bull": ("🐂", 2, 6, "+2 Chips for each $1 you have"),
    "Baron": ("🎩", 3, 8, "Every King held in hand gives x1.5 Mult"),
    "The Duo": ("👯", 3, 8, "x2 Mult if the played hand contains a Pair"),
    "The Trio": ("🎺", 3, 8, "x3 Mult if the played hand contains a Three of a Kind"),
    "The Family": ("🏠", 3, 8, "x4 Mult if the played hand contains a Four of a Kind"),
    "The Order": ("📏", 3, 8, "x3 Mult if the played hand contains a Straight"),
    "The Tribe": ("🏕️", 3, 8, "x2 Mult if the played hand contains a Flush"),
    "Blueprint": ("📘", 3, 10, "Copies the ability of the Joker to its right"),
}
JOKER_START = {"Ice Cream": 100, "Popcorn": 20, "Rocket": 1}
SUIT_JOKERS = {"Greedy Joker": "D", "Lusty Joker": "H", "Wrathful Joker": "S", "Gluttonous Joker": "C"}
TYPE_MULT = {"Jolly Joker": ("Pair", 8), "Zany Joker": ("Three of a Kind", 12), "Mad Joker": ("Two Pair", 10),
             "Crazy Joker": ("Straight", 12), "Droll Joker": ("Flush", 10)}
TYPE_CHIPS = {"Sly Joker": ("Pair", 50), "Wily Joker": ("Three of a Kind", 100), "Clever Joker": ("Two Pair", 80),
              "Devious Joker": ("Straight", 100), "Crafty Joker": ("Flush", 80)}
TYPE_X = {"The Duo": ("Pair", 2), "The Trio": ("Three of a Kind", 3), "The Family": ("Four of a Kind", 4),
          "The Order": ("Straight", 3), "The Tribe": ("Flush", 2)}

# name: (emoji, fewest cards to select, most, what it does)
TAROTS = {
    "The Fool": ("🎒", 0, 0, "Creates a copy of the last Tarot or Planet card used (not The Fool)"),
    "The Magician": ("🪄", 1, 2, "Turns up to 2 selected cards into Lucky Cards"),
    "The High Priestess": ("📿", 0, 0, "Creates up to 2 random Planet cards"),
    "The Empress": ("👑", 1, 2, "Turns up to 2 selected cards into Mult Cards"),
    "The Emperor": ("🤴", 0, 0, "Creates up to 2 random Tarot cards"),
    "The Hierophant": ("⛪", 1, 2, "Turns up to 2 selected cards into Bonus Cards"),
    "The Lovers": ("💞", 1, 1, "Turns 1 selected card into a Wild Card"),
    "The Chariot": ("🛞", 1, 1, "Turns 1 selected card into a Steel Card"),
    "Justice": ("⚖️", 1, 1, "Turns 1 selected card into a Glass Card"),
    "The Hermit": ("🏮", 0, 0, "Doubles your money (max +$20)"),
    "The Wheel of Fortune": ("🎡", 0, 0, "1 in 4 chance to give a random Joker Foil, Holographic or Polychrome"),
    "Strength": ("💪", 1, 2, "Raises the rank of up to 2 selected cards by 1"),
    "The Hanged Man": ("🙃", 1, 2, "Destroys up to 2 selected cards"),
    "Death": ("💀", 2, 2, "Select 2 cards: the left one becomes a copy of the right one"),
    "Temperance": ("🍷", 0, 0, "Gives the total sell value of your Jokers (max $50)"),
    "The Devil": ("👿", 1, 1, "Turns 1 selected card into a Gold Card"),
    "The Tower": ("🗼", 1, 1, "Turns 1 selected card into a Stone Card"),
    "The Star": ("⭐", 1, 3, "Turns up to 3 selected cards into ♦ Diamonds"),
    "The Moon": ("🌙", 1, 3, "Turns up to 3 selected cards into ♣ Clubs"),
    "The Sun": ("☀️", 1, 3, "Turns up to 3 selected cards into ♥ Hearts"),
    "Judgement": ("📯", 0, 0, "Creates a random Joker"),
    "The World": ("🌍", 1, 3, "Turns up to 3 selected cards into ♠ Spades"),
}
ENH_TAROT = {"The Magician": "lucky", "The Empress": "mult", "The Hierophant": "bonus", "The Lovers": "wild",
             "The Chariot": "steel", "Justice": "glass", "The Devil": "gold", "The Tower": "stone"}
SUIT_TAROT = {"The Star": "D", "The Moon": "C", "The Sun": "H", "The World": "S"}

# name: (colour, size x the ante's base, first ante, what it does)
BOSSES = {
    "The Hook": ("#A84024", 2, 1, "Discards 2 random cards held in hand after every hand played"),
    "The Club": ("#8FA35A", 2, 1, "All ♣ Club cards are debuffed"),
    "The Goad": ("#B95B9B", 2, 1, "All ♠ Spade cards are debuffed"),
    "The Head": ("#9C88AE", 2, 1, "All ♥ Heart cards are debuffed"),
    "The Window": ("#9A9283", 2, 1, "All ♦ Diamond cards are debuffed"),
    "The Psychic": ("#D9A82C", 2, 1, "Hands must have 5 cards"),
    "The Manacle": ("#575757", 2, 1, "-1 hand size"),
    "The Wall": ("#8A59A5", 4, 2, "Extra large blind"),
    "The Water": ("#5FA3BF", 2, 2, "Start with 0 discards"),
    "The Arm": ("#6865F3", 2, 2, "Lowers the level of each poker hand you play"),
    "The Flint": ("#E56A2F", 2, 2, "Base Chips and Mult are halved"),
    "The Needle": ("#5C6E31", 1, 2, "Play only 1 hand"),
    "The Mouth": ("#AE718E", 2, 2, "Play only 1 kind of poker hand this round"),
    "The Eye": ("#4B71E4", 2, 3, "No repeated poker hands this round"),
    "The Tooth": ("#B52D2D", 2, 3, "Lose $1 for every card played"),
    "The Plant": ("#709284", 2, 4, "All face cards are debuffed"),
    "The Serpent": ("#439A4F", 2, 5, "After every play or discard, always draw 3 cards"),
    "The Ox": ("#B95C08", 2, 6, "Playing your most played poker hand sets your money to $0"),
}
SHOWDOWN = {    # (the final boss of every 8th ante)
    "Violet Vessel": ("#8A71E1", 6, 8, "Very large blind"),
    "Verdant Leaf": ("#56A786", 2, 8, "All cards are debuffed until you sell a Joker"),
    "Crimson Heart": ("#AC3232", 2, 8, "One random Joker is disabled every hand"),
}
SUIT_BOSS = {"The Club": "C", "The Goad": "S", "The Head": "H", "The Window": "D"}

TAGS = {
    "Uncommon Tag": ("🟩", "The next shop has a free Uncommon Joker"),
    "Rare Tag": ("🟥", "The next shop has a free Rare Joker"),
    "Investment Tag": ("📈", "Gain $25 after beating the next Boss Blind"),
    "Economy Tag": ("💰", "Doubles your money (max +$40)"),
    "Charm Tag": ("🔮", "Opens a free Mega Arcana Pack"),
    "Meteor Tag": ("☄️", "Opens a free Mega Celestial Pack"),
    "Buffoon Tag": ("🤡", "Opens a free Mega Buffoon Pack"),
    "Standard Tag": ("🂡", "Opens a free Mega Standard Pack"),
    "Handy Tag": ("🤚", "Gives $1 for every hand played this run"),
    "Garbage Tag": ("🗑️", "Gives $1 for every unused discard this run"),
    "Juggle Tag": ("🤹", "+3 hand size next round"),
    "Coupon Tag": ("🎟️", "Cards and packs in the next shop are free"),
    "D6 Tag": ("🎲", "Rerolls in the next shop start at $0"),
    "Speed Tag": ("⏩", "Gives $5 for every Blind you've skipped this run"),
}
PACK_TAGS = {"Charm Tag": "Arcana", "Meteor Tag": "Celestial", "Buffoon Tag": "Buffoon", "Standard Tag": "Standard"}

VOUCHERS = {
    "Overstock": ("📦", "+1 card slot in the shop"),
    "Clearance Sale": ("🏷️", "Everything in the shop is 25% off"),
    "Reroll Surplus": ("🔁", "Rerolls cost $2 less"),
    "Crystal Ball": ("🔮", "+1 consumable slot"),
    "Grabber": ("🖐️", "+1 hand every round"),
    "Wasteful": ("🗑️", "+1 discard every round"),
    "Tarot Merchant": ("🃏", "Tarot cards turn up twice as often in the shop"),
    "Planet Merchant": ("🪐", "Planet cards turn up twice as often in the shop"),
    "Seed Money": ("🌱", "Interest can reach $10 a round"),
    "Paint Brush": ("🖌️", "+1 hand size"),
    "Antimatter": ("⚛️", "+1 Joker slot"),
    "Blank": ("⬜", "Does nothing?"),
}

DECKS = {
    "Red Deck": ("#D9473C", "+1 discard every round"),
    "Blue Deck": ("#2F78C4", "+1 hand every round"),
    "Yellow Deck": ("#E3B23C", "Start with an extra $10"),
    "Green Deck": ("#3C9E5C", "At the end of each round, $2 per hand and $1 per discard left; no interest"),
    "Black Deck": ("#2B2B33", "+1 Joker slot; -1 hand every round"),
    "Abandoned Deck": ("#6E7F6A", "No face cards in your deck"),
    "Checkered Deck": ("#B03A54", "26 ♠ Spades and 26 ♥ Hearts"),
    "Erratic Deck": ("#8A5CC2", "Every card's rank and suit is random"),
}

# kind: (emoji, colour, what's inside); size: (prefix, price, cards shown, picks)
PACKS = {"Arcana": ("🔮", "#7A4FA8", "Tarot cards, used straight away"),
         "Celestial": ("🌌", "#2C5A9E", "Planet cards, used straight away"),
         "Buffoon": ("🤡", "#C2453B", "Jokers"),
         "Standard": ("🂡", "#4F6E80", "playing cards to add to your deck")}
PACK_SIZES = {"normal": ("", 4, 3, 1), "jumbo": ("Jumbo ", 6, 5, 1), "mega": ("Mega ", 8, 5, 2)}
PACK_WEIGHTS = [("Arcana", "normal", 4), ("Arcana", "jumbo", 2), ("Arcana", "mega", 0.5),
                ("Celestial", "normal", 4), ("Celestial", "jumbo", 2), ("Celestial", "mega", 0.5),
                ("Buffoon", "normal", 1.2), ("Buffoon", "jumbo", 0.6), ("Buffoon", "mega", 0.15),
                ("Standard", "normal", 4), ("Standard", "jumbo", 2), ("Standard", "mega", 0.5)]

ANTE_BASE = [300, 800, 2000, 5000, 11000, 20000, 35000, 50000]
ANTE_LATE = [110000, 560000, 7200000, 300000000]


def ante_base(ante):
    if ante <= 8:
        return ANTE_BASE[max(1, ante) - 1]
    if ante - 9 < len(ANTE_LATE):
        return ANTE_LATE[ante - 9]
    return ANTE_LATE[-1] * 40 ** (ante - 12)


def pack_name(kind, size):
    return f"{PACK_SIZES[size][0]}{kind} Pack"


class Round:
    """One blind being played. The card lists hold the run's own card dicts (so a tarot changes the deck too)."""
    LISTS = ("draw", "hand", "discard", "played")

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def to_json(self):
        d = dict(self.__dict__)
        for k in self.LISTS:
            d[k] = [c["id"] for c in d[k]]
        return d

    @classmethod
    def from_json(cls, d, cards):
        d = dict(d)
        for k in cls.LISTS:
            d[k] = [cards[i] for i in d[k] if i in cards]
        return cls(**d)


class Tally:
    """The chips and the mult as a hand is scored, and every step of it (the window replays them one by one)."""

    def __init__(self, run, chips, mult):
        self.run = run
        self.chips = chips
        self.mult = mult
        self.events = []

    def apply(self, at, kind, v):
        if kind == "chips":
            self.chips += v
            text = f"+{v}"
        elif kind == "mult":
            self.mult += v
            text = f"+{v} Mult"
        elif kind == "xmult":
            self.mult *= v
            text = f"x{v:g} Mult"
        elif kind == "money":
            self.run.money += v
            text = f"+${v}" if v >= 0 else f"-${-v}"
        else:
            text = v
        self.events.append({"at": list(at), "text": text, "kind": kind, "chips": self.chips, "mult": self.mult})


class Run:
    """A whole run: the deck, the jokers, the money, the antes, and whatever's happening right now (`stage`)."""

    def __init__(self, deck="Red Deck", seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)
        self.deck_name = deck
        self.next_id = 1
        self.money = 4 + (10 if deck == "Yellow Deck" else 0)
        self.ante = 1
        self.blind = 0                      # 0 small, 1 big, 2 boss
        self.round_no = 1
        self.hands_base = 4 + (deck == "Blue Deck") - (deck == "Black Deck")
        self.discards_base = 3 + (deck == "Red Deck")
        self.hand_size_base = 8
        self.joker_slots = 5 + (deck == "Black Deck")
        self.cons_slots = 2
        self.shop_slots = 2
        self.jokers = []
        self.consumables = []
        self.vouchers = []
        self.pending_tags = []
        self.levels = {h[0]: 1 for h in HANDS}
        self.played = {h[0]: 0 for h in HANDS}
        self.seen_bosses = []
        self.boss = None
        self.skip_tags = []
        self.voucher_offer = None
        self.blind_state = ["", "", ""]     # "skipped" / "beaten"
        self.shop = None
        self.pack = None
        self.cash = []
        self.notes = []
        self.stage = "blind"                # blind / round / cashout / shop / pack / over
        self.last_was_boss = False
        self.won = False                    # (just beat ante 8: the window offers endless mode)
        self.endless = False
        self.juggle = 0
        self.last_used = None               # (for The Fool)
        self.extinct = False                # (Gros Michel's gone: Cavendish can turn up)
        self.hands_total = 0
        self.discards_unused = 0
        self.skips = 0
        self.best_hand = 0
        self.deck = self._make_deck(deck)
        self.rnd = None
        self._new_ante()

    # ---- saving ----
    def to_json(self):
        d = {k: v for k, v in self.__dict__.items() if k not in ("rng", "rnd")}
        st = self.rng.getstate()
        d["rng"] = [st[0], list(st[1]), st[2]]
        d["rnd"] = self.rnd.to_json() if self.rnd else None
        return d

    @classmethod
    def from_json(cls, d):
        run = cls.__new__(cls)
        d = dict(d)
        st = d.pop("rng")
        rnd = d.pop("rnd")
        run.__dict__.update(d)
        run.rng = random.Random()
        run.rng.setstate((st[0], tuple(st[1]), st[2]))
        run.rnd = Round.from_json(rnd, {c["id"]: c for c in run.deck}) if rnd else None
        return run

    # ---- cards ----
    def new_card(self, r, s, enh=None, ed=None):
        c = {"r": r, "s": s, "enh": enh, "ed": ed, "bonus": 0, "id": self.next_id}
        self.next_id += 1
        return c

    def _make_deck(self, name):
        cards = []
        for s in SUITS:
            for r in range(2, 15):
                if name == "Abandoned Deck" and r in FACE:
                    continue
                ss, rr = s, r
                if name == "Checkered Deck":
                    ss = "S" if s in "SC" else "H"
                elif name == "Erratic Deck":
                    rr, ss = self.rng.randint(2, 14), self.rng.choice(SUITS)
                cards.append(self.new_card(rr, ss))
        return cards

    def random_card(self):
        c = self.new_card(self.rng.randint(2, 14), self.rng.choice(SUITS))
        if self.rng.random() < 0.4:
            c["enh"] = self.rng.choice(list(ENHANCEMENTS))
        x = self.rng.random()
        c["ed"] = "poly" if x < 0.012 else "holo" if x < 0.04 else "foil" if x < 0.08 else None
        return c

    def has(self, key):
        return any(j["k"] == key for j in self.jokers)

    def count(self, key):
        return sum(j["k"] == key for j in self.jokers)

    def suit_is(self, c, s):
        if c["enh"] == "stone":
            return False
        if c["enh"] == "wild":
            return True
        if self.has("Smeared Joker"):
            return (c["s"] in "HD") == (s in "HD")
        return c["s"] == s

    def is_face(self, c):
        return c["enh"] != "stone" and (c["r"] in FACE or self.has("Pareidolia"))

    def debuffed(self, c):
        r = self.rnd
        if r is None or not r.boss:
            return False
        if r.boss == "Verdant Leaf" and r.leaf:
            return True
        if r.boss in SUIT_BOSS and self.suit_is(c, SUIT_BOSS[r.boss]):
            return True
        return r.boss == "The Plant" and self.is_face(c)

    # ---- jokers, tarots, planets ----
    def new_joker(self, key, ed=None):
        cost = JOKERS[key][2] + EDITION_COST.get(ed, 0)
        j = {"k": key, "ed": ed, "st": {"v": JOKER_START.get(key, 0)}, "id": self.next_id, "sell": max(1, cost // 2)}
        self.next_id += 1
        return j

    def _joker_allowed(self, k):
        if k == "Cavendish":
            return self.extinct
        if k == "Gros Michel":
            return not self.extinct
        return True

    def random_joker_key(self, rarity=None, exclude=()):
        if rarity is None:
            x = self.rng.random()
            rarity = 1 if x < 0.7 else 2 if x < 0.95 else 3
        owned = {j["k"] for j in self.jokers} | set(exclude)
        pool = [k for k, v in JOKERS.items() if v[1] == rarity and k not in owned and self._joker_allowed(k)]
        if not pool:
            pool = [k for k, v in JOKERS.items() if v[1] == rarity and self._joker_allowed(k)]
        return self.rng.choice(pool)

    def roll_edition(self):
        x = self.rng.random()
        return "poly" if x < 0.003 else "holo" if x < 0.017 else "foil" if x < 0.037 else None

    def planet_pool(self):
        return [p for p, h in PLANETS.items() if h not in SECRET or self.played[h] > 0]

    def joker_status(self, j):
        """What a joker's worth right now, for its tooltip (or None)."""
        k, v = j["k"], j["st"].get("v", 0)
        r = self.rnd
        if k in ("Ride the Bus", "Green Joker", "Popcorn"):
            return f"Currently +{v} Mult"
        if k in ("Ice Cream", "Square Joker", "Runner"):
            return f"Currently +{v} Chips"
        if k == "Constellation":
            return f"Currently x{1 + 0.1 * v:.1f} Mult"
        if k == "Rocket":
            return f"Currently ${v}"
        if k == "Abstract Joker":
            return f"Currently +{3 * len(self.jokers)} Mult"
        if k == "Blue Joker":
            return f"Currently +{2 * (len(r.draw) if r else len(self.deck))} Chips"
        if k == "Bull":
            return f"Currently +{2 * max(0, self.money)} Chips"
        if k == "Bootstraps":
            return f"Currently +{2 * max(0, self.money // 5)} Mult"
        if k == "Steel Joker":
            return f"Currently x{1 + 0.2 * sum(c['enh'] == 'steel' for c in self.deck):.1f} Mult"
        if k == "Joker Stencil":
            return f"Currently x{self.joker_slots - len(self.jokers) + self.count('Joker Stencil')} Mult"
        if k == "Cloud 9":
            return f"Currently ${self._nines()}"
        if k == "Supernova":
            return None
        return None

    def _nines(self):
        return sum(c["r"] == 9 and c["enh"] != "stone" for c in self.deck)

    # ---- antes and blinds ----
    def _new_ante(self):
        if self.ante % 8 == 0:
            pool = list(SHOWDOWN)
        else:
            pool = [b for b, v in BOSSES.items() if v[2] <= self.ante and b not in self.seen_bosses]
            if not pool:
                self.seen_bosses = []
                pool = [b for b, v in BOSSES.items() if v[2] <= self.ante]
        self.boss = self.rng.choice(pool)
        self.seen_bosses.append(self.boss)
        self.skip_tags = [self.rng.choice(list(TAGS)), self.rng.choice(list(TAGS))]
        left = [v for v in VOUCHERS if v not in self.vouchers]
        self.voucher_offer = self.rng.choice(left) if left else None
        self.blind_state = ["", "", ""]

    def boss_info(self, name=None):
        name = name or self.boss
        return BOSSES.get(name) or SHOWDOWN[name]

    def blinds(self):
        base = ante_base(self.ante)
        colour, size, _a, text = self.boss_info()
        return [{"kind": "small", "name": "Small Blind", "target": base, "reward": 3, "colour": "#2E6DA4",
                 "text": ""},
                {"kind": "big", "name": "Big Blind", "target": int(base * 1.5), "reward": 4, "colour": "#D08B1A",
                 "text": ""},
                {"kind": "boss", "name": self.boss, "target": int(base * size),
                 "reward": 8 if self.boss in SHOWDOWN else 5, "colour": colour, "text": text}]

    def select_blind(self):
        b = self.blinds()[self.blind]
        boss = b["name"] if b["kind"] == "boss" else None
        r = Round(kind=b["kind"], name=b["name"], target=b["target"], reward=b["reward"], boss=boss, score=0,
                  hands=self.hands_base + ("Grabber" in self.vouchers),
                  discards=self.discards_base + ("Wasteful" in self.vouchers) + self.count("Drunkard"),
                  hand_size=self.hand_size_base + ("Paint Brush" in self.vouchers) + self.count("Juggler")
                  + self.juggle,
                  draw=list(self.deck), hand=[], discard=[], played=[], used_types=[], discards_used=0,
                  hands_played=0, leaf=boss == "Verdant Leaf", disabled=None, broken=[], sort="rank", ox=None)
        self.juggle = 0
        if self.has("Burglar"):
            r.hands += 3 * self.count("Burglar")
            r.discards = 0
        if boss == "The Water":
            r.discards = 0
        if boss == "The Needle":
            r.hands = 1
        if boss == "The Manacle":
            r.hand_size -= 1
        if boss == "The Ox" and max(self.played.values()) > 0:
            r.ox = max(self.played, key=lambda h: self.played[h])
        self.rng.shuffle(r.draw)
        self.rnd = r
        self.stage = "round"
        self.draw_up()
        self._crimson()

    def skip_blind(self):
        tag = self.skip_tags[self.blind]
        self.blind_state[self.blind] = "skipped"
        self.blind += 1
        self.skips += 1
        return self.apply_tag(tag)

    def apply_tag(self, tag):
        if tag == "Economy Tag":
            gain = min(max(0, self.money), 40)
        elif tag == "Handy Tag":
            gain = self.hands_total
        elif tag == "Garbage Tag":
            gain = self.discards_unused
        elif tag == "Speed Tag":
            gain = 5 * self.skips
        else:
            gain = None
        if gain is not None:
            self.money += gain
            return f"{tag}: +${gain}"
        if tag == "Juggle Tag":
            self.juggle += 3
            return "Juggle Tag: +3 hand size next round"
        if tag in PACK_TAGS:
            self.open_pack(PACK_TAGS[tag], "mega", back=self.stage)
            return None
        self.pending_tags.append(tag)
        return f"{tag}: {TAGS[tag][1].lower()}"

    def _crimson(self):
        r = self.rnd
        if r and r.boss == "Crimson Heart":
            r.disabled = self.rng.choice(self.jokers)["id"] if self.jokers else None

    # ---- the hand ----
    def sort_hand(self, mode=None):
        r = self.rnd
        if mode:
            r.sort = mode
        order = {s: i for i, s in enumerate(SUITS)}
        if r.sort == "rank":
            r.hand.sort(key=lambda c: (-(0 if c["enh"] == "stone" else c["r"]), order[c["s"]]))
        elif r.sort == "suit":
            r.hand.sort(key=lambda c: (order[c["s"]], -(0 if c["enh"] == "stone" else c["r"])))

    def draw_up(self, n=None):
        r = self.rnd
        n = r.hand_size - len(r.hand) if n is None else n
        for _ in range(max(0, n)):
            if not r.draw:
                break
            r.hand.append(r.draw.pop())
        self.sort_hand()

    def _straight(self, cards, need):
        gap = 2 if self.has("Shortcut") else 1
        by_rank = {}
        for c in cards:
            by_rank.setdefault(c["r"], c)
        ranks = sorted(by_rank)
        if 14 in by_rank:
            ranks = [1] + ranks
        best, cur = [], []
        for r in ranks:
            cur = cur + [r] if cur and r - cur[-1] <= gap else [r]
            if len(cur) > len(best):
                best = list(cur)
        if len(best) >= need:
            return [by_rank[14 if r == 1 else r] for r in best]
        return []

    def evaluate(self, cards):
        """(poker hand, the cards that score, every poker hand it contains)."""
        ranked = [c for c in cards if c["enh"] != "stone"]
        need = 4 if self.has("Four Fingers") else 5
        groups = {}
        for c in ranked:
            groups.setdefault(c["r"], []).append(c)
        big = sorted(groups.values(), key=lambda g: (len(g), g[0]["r"]), reverse=True)
        sizes = [len(g) for g in big] + [0, 0]
        flush = []
        if len(ranked) >= need:
            for s in SUITS:
                fs = [c for c in ranked if self.suit_is(c, s)]
                if len(fs) >= need and len(fs) > len(flush):
                    flush = fs
        straight = self._straight(ranked, need)
        full = sizes[0] >= 3 and sizes[1] >= 2
        contains = set()
        if sizes[0] >= 2:
            contains.add("Pair")
        if sizes[1] >= 2:
            contains.add("Two Pair")
        if sizes[0] >= 3:
            contains.add("Three of a Kind")
        if sizes[0] >= 4:
            contains.add("Four of a Kind")
        if straight:
            contains.add("Straight")
        if flush:
            contains.add("Flush")
        if full:
            contains.add("Full House")
        if straight and flush:
            contains.add("Straight Flush")
        if sizes[0] >= 5 and flush:
            name, sc = "Flush Five", ranked
        elif full and flush:
            name, sc = "Flush House", ranked
        elif sizes[0] >= 5:
            name, sc = "Five of a Kind", big[0]
        elif straight and flush:
            name, sc = "Straight Flush", straight + [c for c in flush if c not in straight]
        elif sizes[0] >= 4:
            name, sc = "Four of a Kind", big[0]
        elif full:
            name, sc = "Full House", big[0] + big[1]
        elif flush:
            name, sc = "Flush", flush
        elif straight:
            name, sc = "Straight", straight
        elif sizes[0] >= 3:
            name, sc = "Three of a Kind", big[0]
        elif sizes[1] >= 2:
            name, sc = "Two Pair", big[0] + big[1]
        elif sizes[0] >= 2:
            name, sc = "Pair", big[0]
        else:
            name, sc = "High Card", ([max(ranked, key=lambda c: c["r"])] if ranked else [])
        contains.add(name)
        ids = {c["id"] for c in sc}
        scoring = list(cards) if self.has("Splash") else [c for c in cards if c["id"] in ids or c["enh"] == "stone"]
        return name, scoring, contains

    def hand_value(self, name):
        chips, mult, lc, lm = HAND_INFO[name]
        lv = self.levels[name]
        return chips + lc * (lv - 1), mult + lm * (lv - 1)

    def preview(self, cards):
        """What a selection would be: (poker hand, level, chips, mult) before any jokers."""
        if not cards:
            return None
        name = self.evaluate(cards)[0]
        chips, mult = self.hand_value(name)
        if self.rnd and self.rnd.boss == "The Flint":
            chips, mult = (chips + 1) // 2, (mult + 1) // 2
        return name, self.levels[name], chips, mult

    # ---- scoring ----
    def _active(self):
        """(position, the ability it uses, whose state) for each joker that counts this hand - Blueprint resolved."""
        out = []
        r = self.rnd
        for i, j in enumerate(self.jokers):
            if j.get("dead") or (r and r.disabled == j["id"]):
                continue
            src, k = j, i
            while src is not None and src["k"] == "Blueprint":
                k += 1
                src = self.jokers[k] if k < len(self.jokers) else None
            out.append((i, src["k"] if src else None, src))
        return out

    def _on_card(self, key, c, first_face):
        """A joker's ability when a played card scores."""
        stone = c["enh"] == "stone"
        r = None if stone else c["r"]
        if key in SUIT_JOKERS:
            return [("mult", 3)] if self.suit_is(c, SUIT_JOKERS[key]) else []
        if key == "Fibonacci" and r in (14, 2, 3, 5, 8):
            return [("mult", 8)]
        if key == "Scary Face" and self.is_face(c):
            return [("chips", 30)]
        if key == "Smiley Face" and self.is_face(c):
            return [("mult", 5)]
        if key == "Even Steven" and r in (2, 4, 6, 8, 10):
            return [("mult", 4)]
        if key == "Odd Todd" and r in (14, 3, 5, 7, 9):
            return [("chips", 31)]
        if key == "Scholar" and r == 14:
            return [("chips", 20), ("mult", 4)]
        if key == "Walkie Talkie" and r in (10, 4):
            return [("chips", 10), ("mult", 4)]
        if key == "Photograph" and first_face is not None and c["id"] == first_face:
            return [("xmult", 2)]
        if key == "Business Card" and self.is_face(c) and self.rng.random() < 0.5:
            return [("money", 2)]
        if key == "Rough Gem" and self.suit_is(c, "D"):
            return [("money", 1)]
        if key == "Hiker":
            c["bonus"] += 5
            return [("info", "Upgrade!")]
        return []

    def _independent(self, key, src, name, contains, cards):
        r = self.rnd
        v = src["st"].get("v", 0) if src else 0
        if key == "Joker":
            return [("mult", 4)]
        if key in TYPE_MULT:
            h, n = TYPE_MULT[key]
            return [("mult", n)] if h in contains else []
        if key in TYPE_CHIPS:
            h, n = TYPE_CHIPS[key]
            return [("chips", n)] if h in contains else []
        if key in TYPE_X:
            h, n = TYPE_X[key]
            return [("xmult", n)] if h in contains else []
        if key == "Half Joker":
            return [("mult", 20)] if len(cards) <= 3 else []
        if key == "Banner":
            return [("chips", 30 * r.discards)] if r.discards > 0 else []
        if key == "Mystic Summit":
            return [("mult", 15)] if r.discards == 0 else []
        if key == "Misprint":
            return [("mult", self.rng.randint(0, 23))]
        if key == "Abstract Joker":
            return [("mult", 3 * len(self.jokers))]
        if key == "Gros Michel":
            return [("mult", 15)]
        if key == "Cavendish":
            return [("xmult", 3)]
        if key == "Supernova":
            return [("mult", self.played[name])]
        if key in ("Ride the Bus", "Green Joker", "Popcorn"):
            return [("mult", v)] if v > 0 else []
        if key in ("Ice Cream", "Square Joker", "Runner"):
            return [("chips", v)] if v > 0 else []
        if key == "Blue Joker":
            return [("chips", 2 * len(r.draw))] if r.draw else []
        if key == "Bull":
            return [("chips", 2 * self.money)] if self.money > 0 else []
        if key == "Bootstraps":
            return [("mult", 2 * (self.money // 5))] if self.money >= 5 else []
        if key == "Steel Joker":
            n = sum(c["enh"] == "steel" for c in self.deck)
            return [("xmult", round(1 + 0.2 * n, 2))] if n else []
        if key == "Constellation":
            return [("xmult", round(1 + 0.1 * v, 2))] if v else []
        if key == "Blackboard":
            ok = all(self.suit_is(c, "S") or self.suit_is(c, "C") for c in r.hand)
            return [("xmult", 3)] if ok else []
        if key == "Acrobat":
            return [("xmult", 3)] if r.hands == 0 else []
        if key == "Joker Stencil":
            x = self.joker_slots - len(self.jokers) + self.count("Joker Stencil")
            return [("xmult", x)] if x > 1 else []
        return []

    def play(self, idx):
        """Play the cards at these hand positions. Returns what happened, step by step, for the window to replay;
        call after_play() once it has."""
        r = self.rnd
        idx = sorted(set(idx))
        if r is None or not 1 <= len(idx) <= 5 or r.hands <= 0 or r.played:
            return None
        cards = [r.hand[i] for i in idx]
        ids = {c["id"] for c in cards}
        r.hand = [c for c in r.hand if c["id"] not in ids]
        r.played = cards
        r.hands -= 1
        r.hands_played += 1
        self.hands_total += 1
        name, scoring, contains = self.evaluate(cards)
        boss = r.boss
        blocked = ((boss == "The Psychic" and len(cards) < 5) or (boss == "The Eye" and name in r.used_types)
                   or (boss == "The Mouth" and r.used_types and name != r.used_types[0]))
        if name not in r.used_types:
            r.used_types.append(name)
        t = Tally(self, 0, 0)
        if boss == "The Tooth":
            t.apply(("hand",), "money", -len(cards))
        if boss == "The Ox" and name == r.ox:
            self.money = 0
            t.apply(("hand",), "info", "$0!")
        self.played[name] += 1
        if boss == "The Arm" and self.levels[name] > 1:
            self.levels[name] -= 1
            t.apply(("hand",), "info", "Level down!")
        chips, mult = self.hand_value(name)
        if boss == "The Flint":
            chips, mult = (chips + 1) // 2, (mult + 1) // 2
        t.chips, t.mult = chips, mult
        res = {"hand": name, "level": self.levels[name], "base": (chips, mult), "scoring": [c["id"] for c in scoring]}
        if blocked:
            t.apply(("hand",), "info", "Not allowed!")
            total = 0
        else:
            total = self._score(t, name, cards, scoring, contains)
        r.score += total
        self.best_hand = max(self.best_hand, total)
        res["events"] = t.events
        res["total"] = total
        return res

    def _score(self, t, name, cards, scoring, contains):
        r = self.rnd
        active = self._active()
        pos = {c["id"]: i for i, c in enumerate(cards)}
        live = [c for c in scoring if not self.debuffed(c)]
        # the jokers that grow as you play
        for i, j in enumerate(self.jokers):
            k = j["k"]
            if k == "Ride the Bus":
                if any(self.is_face(c) for c in live):
                    if j["st"]["v"]:
                        j["st"]["v"] = 0
                        t.apply(("joker", i), "info", "Reset")
                else:
                    j["st"]["v"] += 1
                    t.apply(("joker", i), "info", "Upgrade!")
            elif k == "Green Joker":
                j["st"]["v"] += 1
                t.apply(("joker", i), "info", "+1 Mult")
            elif k == "Square Joker" and len(cards) == 4:
                j["st"]["v"] += 4
                t.apply(("joker", i), "info", "Upgrade!")
            elif k == "Runner" and "Straight" in contains:
                j["st"]["v"] += 15
                t.apply(("joker", i), "info", "Upgrade!")
        first_face = next((c["id"] for c in live if self.is_face(c)), None)
        final = r.hands == 0
        for n, c in enumerate(scoring):
            at = ("played", pos[c["id"]])
            if self.debuffed(c):
                t.apply(at, "info", "Debuffed")
                continue
            again = []
            for i, key, _src in active:
                if ((key == "Hanging Chad" and n == 0) or (key == "Sock and Buskin" and self.is_face(c))
                        or (key == "Hack" and c["enh"] != "stone" and c["r"] in (2, 3, 4, 5))
                        or (key == "Dusk" and final)):
                    again.append(i)
            for rep in range(1 + len(again)):
                if rep:
                    t.apply(("joker", again[rep - 1]), "info", "Again!")
                if c["enh"] == "stone":
                    t.apply(at, "chips", 50 + c["bonus"])
                else:
                    t.apply(at, "chips", rank_chips(c["r"]) + c["bonus"] + (30 if c["enh"] == "bonus" else 0))
                if c["enh"] == "mult":
                    t.apply(at, "mult", 4)
                elif c["enh"] == "glass":
                    t.apply(at, "xmult", 2)
                elif c["enh"] == "lucky":
                    if self.rng.random() < 1 / 5:
                        t.apply(at, "mult", 20)
                    if self.rng.random() < 1 / 15:
                        t.apply(at, "money", 20)
                if c["ed"] == "foil":
                    t.apply(at, "chips", 50)
                elif c["ed"] == "holo":
                    t.apply(at, "mult", 10)
                elif c["ed"] == "poly":
                    t.apply(at, "xmult", 1.5)
                for i, key, _src in active:
                    for kind, v in self._on_card(key, c, first_face):
                        t.apply(at if kind == "info" else ("joker", i), kind, v)
        # cards held in hand
        mimes = sum(key == "Mime" for _i, key, _s in active)
        held = [c for c in r.hand if c["enh"] != "stone"]
        lowest = min(held, key=lambda c: c["r"])["id"] if held else None
        for h, c in enumerate(r.hand):
            if self.debuffed(c):
                continue
            for _rep in range(1 + mimes):
                at = ("held", h)
                if c["enh"] == "steel":
                    t.apply(at, "xmult", 1.5)
                if c["enh"] == "stone":
                    continue
                for i, key, _src in active:
                    if key == "Baron" and c["r"] == 13:
                        t.apply(at, "xmult", 1.5)
                    elif key == "Shoot the Moon" and c["r"] == 12:
                        t.apply(at, "mult", 13)
                    elif key == "Raised Fist" and c["id"] == lowest:
                        t.apply(at, "mult", 2 * rank_chips(c["r"]))
        # the jokers themselves, left to right
        for i, key, src in active:
            j = self.jokers[i]
            if j["ed"] == "foil":
                t.apply(("joker", i), "chips", 50)
            elif j["ed"] == "holo":
                t.apply(("joker", i), "mult", 10)
            for kind, v in self._independent(key, src, name, contains, cards):
                t.apply(("joker", i), kind, v)
            if j["ed"] == "poly":
                t.apply(("joker", i), "xmult", 1.5)
        total = int(t.chips * t.mult)
        # afterwards: glass breaks, ice cream melts
        for c in live:
            if c["enh"] == "glass" and self.rng.random() < 0.25:
                r.broken.append(c["id"])
                t.apply(("played", pos[c["id"]]), "info", "Broken!")
        for i, j in enumerate(self.jokers):
            if j["k"] == "Ice Cream":
                j["st"]["v"] -= 5
                if j["st"]["v"] <= 0:
                    j["dead"] = True
                    t.apply(("joker", i), "info", "Melted!")
        return total

    def after_play(self):
        """The played cards go to the discard pile; then the round's won, lost, or you draw back up."""
        r = self.rnd
        broken = set(r.broken)
        r.discard += [c for c in r.played if c["id"] not in broken]
        if broken:
            self.deck = [c for c in self.deck if c["id"] not in broken]
        r.broken = []
        r.played = []
        self.jokers = [j for j in self.jokers if not j.get("dead")]
        if r.score >= r.target:
            self._win_round()
            return
        if r.hands <= 0:
            self.stage = "over"
            return
        if r.boss == "The Hook":
            for _ in range(min(2, len(r.hand))):
                c = self.rng.choice(r.hand)
                r.hand.remove(c)
                r.discard.append(c)
        self.draw_up(3 if r.boss == "The Serpent" else None)
        self._crimson()
        if not r.hand:
            self.stage = "over"

    def discard(self, idx):
        r = self.rnd
        idx = sorted(set(idx))
        if r is None or r.discards <= 0 or not 1 <= len(idx) <= 5 or r.played:
            return False
        cards = [r.hand[i] for i in idx]
        ids = {c["id"] for c in cards}
        r.hand = [c for c in r.hand if c["id"] not in ids]
        r.discard += cards
        r.discards -= 1
        r.discards_used += 1
        for j in self.jokers:
            if j["k"] == "Green Joker":
                j["st"]["v"] = max(0, j["st"]["v"] - 1)
        self.draw_up(3 if r.boss == "The Serpent" else None)
        if not r.hand:
            self.stage = "over"
        return True

    def _win_round(self):
        r = self.rnd
        green = self.deck_name == "Green Deck"
        lines = [(r.name, r.reward)]
        if r.hands:
            lines.append((f"{r.hands} hands left (${2 if green else 1} each)", r.hands * (2 if green else 1)))
        if green and r.discards:
            lines.append((f"{r.discards} discards left ($1 each)", r.discards))
        for j in self.jokers:
            k = j["k"]
            if k == "Golden Joker":
                lines.append(("Golden Joker", 4))
            elif k == "Cloud 9" and self._nines():
                lines.append(("Cloud 9", self._nines()))
            elif k == "Rocket":
                lines.append(("Rocket", j["st"]["v"]))
            elif k == "Delayed Gratification" and r.discards_used == 0 and r.discards:
                lines.append(("Delayed Gratification", 2 * r.discards))
        gold = sum(3 for c in r.hand if c["enh"] == "gold" and not self.debuffed(c))
        if gold:
            lines.append(("Gold Cards held in hand", gold))
        if not green:
            cap = 10 if "Seed Money" in self.vouchers else 5
            interest = min(max(0, self.money) // 5, cap)
            if interest:
                lines.append((f"Interest ($1 for every $5, max ${cap})", interest))
                for _ in range(self.count("To the Moon")):
                    lines.append(("To the Moon", interest))
        boss = r.kind == "boss"
        if boss:
            while "Investment Tag" in self.pending_tags:
                self.pending_tags.remove("Investment Tag")
                lines.append(("Investment Tag", 25))
        notes = []
        for j in self.jokers:
            k = j["k"]
            if k == "Egg":
                j["sell"] += 3
            elif k == "Popcorn":
                j["st"]["v"] -= 4
                if j["st"]["v"] <= 0:
                    j["dead"] = True
                    notes.append("The Popcorn's all eaten.")
            elif k == "Gros Michel" and self.rng.random() < 1 / 6:
                j["dead"] = True
                self.extinct = True
                notes.append("Gros Michel went extinct!")
            elif k == "Cavendish" and self.rng.random() < 1 / 1000:
                j["dead"] = True
                notes.append("Cavendish went extinct!")
            elif k == "Rocket" and boss:
                j["st"]["v"] += 2
        self.jokers = [j for j in self.jokers if not j.get("dead")]
        self.discards_unused += r.discards
        self.cash = lines
        self.notes = notes
        self.blind_state[self.blind] = "beaten"
        self.last_was_boss = boss
        self.round_no += 1
        self.rnd = None
        self.stage = "cashout"
        if boss and self.ante >= 8 and not self.endless:
            self.won = True

    def cash_total(self):
        return sum(v for _l, v in self.cash)

    def collect(self):
        self.money += self.cash_total()
        self.cash = []
        self.notes = []
        if self.last_was_boss:
            self.ante += 1
            self.blind = 0
            self._new_ante()
        else:
            self.blind += 1
        self._make_shop()
        self.stage = "shop"

    # ---- the shop ----
    def floor(self):
        return -20 if self.has("Credit Card") else 0

    def _price(self, base):
        return max(1, int(base * 0.75)) if "Clearance Sale" in self.vouchers else base

    def _shop_card(self, exclude):
        tw = 8 if "Tarot Merchant" in self.vouchers else 4
        pw = 8 if "Planet Merchant" in self.vouchers else 4
        x = self.rng.random() * (20 + tw + pw)
        if x < 20:
            key = self.random_joker_key(exclude=exclude)
            exclude.add(key)
            j = self.new_joker(key, self.roll_edition())
            base = JOKERS[key][2] + EDITION_COST.get(j["ed"], 0)
            return {"type": "joker", "item": j, "base": base, "price": self._price(base)}
        if x < 20 + tw:
            return {"type": "tarot", "item": self.rng.choice(list(TAROTS)), "base": 3, "price": self._price(3)}
        return {"type": "planet", "item": self.rng.choice(self.planet_pool()), "base": 3, "price": self._price(3)}

    def _pack_item(self):
        x = self.rng.random() * sum(w for *_k, w in PACK_WEIGHTS)
        for kind, size, w in PACK_WEIGHTS:
            x -= w
            if x <= 0:
                break
        base = PACK_SIZES[size][1]
        return {"type": "pack", "kind": kind, "size": size, "base": base, "price": self._price(base)}

    def _make_shop(self):
        ex = set()
        cards = [self._shop_card(ex) for _ in range(self.shop_slots)]
        packs = [self._pack_item(), self._pack_item()]
        reroll = 5 - (2 if "Reroll Surplus" in self.vouchers else 0)
        for tag in list(self.pending_tags):
            if tag in ("Uncommon Tag", "Rare Tag"):
                j = self.new_joker(self.random_joker_key(2 if tag == "Uncommon Tag" else 3), self.roll_edition())
                cards[0] = {"type": "joker", "item": j, "base": 0, "price": 0}
            elif tag == "Coupon Tag":
                for it in cards + packs:
                    it["base"] = it["price"] = 0
            elif tag == "D6 Tag":
                reroll = 0
            else:
                continue
            self.pending_tags.remove(tag)
        voucher = None
        if self.voucher_offer:
            voucher = {"type": "voucher", "item": self.voucher_offer, "base": 10, "price": self._price(10)}
        self.shop = {"cards": cards, "packs": packs, "voucher": voucher, "reroll": reroll,
                     "free": self.count("Chaos the Clown")}

    def reroll(self):
        s = self.shop
        if s["free"] > 0:
            s["free"] -= 1
        elif self.money - s["reroll"] < self.floor():
            return "Not enough money"
        else:
            self.money -= s["reroll"]
            s["reroll"] += 1
        ex = set()
        s["cards"] = [self._shop_card(ex) for _ in range(self.shop_slots)]
        return None

    def buy(self, where, i=0):
        s = self.shop
        item = s["voucher"] if where == "voucher" else s[where][i]
        if item is None:
            return "Sold out"
        price = item["price"]
        if price > 0 and self.money - price < self.floor():
            return "Not enough money"
        t = item["type"]
        if t == "joker" and len(self.jokers) >= self.joker_slots:
            return "No room for another Joker"
        if t in ("tarot", "planet") and len(self.consumables) >= self.cons_slots:
            return "No room for another consumable"
        self.money -= price
        if where == "voucher":
            s["voucher"] = None
            self.voucher_offer = None
        else:
            s[where][i] = None
        if t == "joker":
            item["item"]["sell"] = max(1, price // 2)
            self.jokers.append(item["item"])
        elif t in ("tarot", "planet"):
            self.consumables.append({"k": item["item"], "type": t})
        elif t == "pack":
            self.open_pack(item["kind"], item["size"], back="shop")
        elif t == "voucher":
            self._apply_voucher(item["item"])
        return None

    def _apply_voucher(self, v):
        self.vouchers.append(v)
        s = self.shop
        if v == "Overstock":
            self.shop_slots += 1
            if s:
                s["cards"].append(self._shop_card({j["item"]["k"] for j in s["cards"] if j and j["type"] == "joker"}))
        elif v == "Crystal Ball":
            self.cons_slots += 1
        elif v == "Antimatter":
            self.joker_slots += 1
        elif v == "Reroll Surplus" and s:
            s["reroll"] = max(0, s["reroll"] - 2)
        elif v == "Clearance Sale" and s:
            for it in s["cards"] + s["packs"]:
                if it and it["price"]:
                    it["price"] = self._price(it["base"])

    def next_round(self):
        self.shop = None
        self.stage = "blind"

    def sell_joker(self, i):
        j = self.jokers.pop(i)
        self.money += j["sell"]
        if self.rnd and self.rnd.boss == "Verdant Leaf":
            self.rnd.leaf = False
        if self.rnd and self.rnd.disabled == j["id"]:
            self.rnd.disabled = None
        return j

    def sell_consumable(self, i):
        self.consumables.pop(i)
        self.money += 1

    # ---- packs ----
    def open_pack(self, kind, size, back):
        _p, _price, n, picks = PACK_SIZES[size]
        if kind == "Buffoon":
            n = 2 if size == "normal" else 4
        if kind == "Arcana":
            choices = [{"type": "tarot", "item": t} for t in self.rng.sample(list(TAROTS), n)]
        elif kind == "Celestial":
            pool = self.planet_pool()
            names = self.rng.sample(pool, n) if len(pool) >= n else [self.rng.choice(pool) for _ in range(n)]
            choices = [{"type": "planet", "item": p} for p in names]
        elif kind == "Buffoon":
            ex = set()
            choices = []
            for _ in range(n):
                key = self.random_joker_key(exclude=ex)
                ex.add(key)
                choices.append({"type": "joker", "item": self.new_joker(key, self.roll_edition())})
        else:
            choices = [{"type": "card", "item": self.random_card()} for _ in range(n)]
        hand = []
        if kind == "Arcana":                       # (a hand to use the tarots on)
            pile = list(self.deck)
            self.rng.shuffle(pile)
            size_ = self.hand_size_base + ("Paint Brush" in self.vouchers) + self.count("Juggler")
            hand = [c["id"] for c in pile[:size_]]
        self.pack = {"kind": kind, "size": size, "choices": choices, "picks": picks, "back": back, "hand": hand}
        self.stage = "pack"

    def pack_hand(self):
        if not self.pack:
            return []
        cards = {c["id"]: c for c in self.deck}
        return [cards[i] for i in self.pack["hand"] if i in cards]

    def pack_pick(self, i, sel=()):
        pk = self.pack
        ch = pk["choices"][i]
        msg = None
        if ch["type"] == "tarot":
            ok, msg = self.use_tarot(ch["item"], list(sel))
            if not ok:
                return False, msg
        elif ch["type"] == "planet":
            msg = self.use_planet(ch["item"])
        elif ch["type"] == "joker":
            if len(self.jokers) >= self.joker_slots:
                return False, "No room for another Joker"
            self.jokers.append(ch["item"])
        else:
            self.deck.append(ch["item"])
            msg = "Added to your deck"
        pk["choices"].pop(i)
        pk["picks"] -= 1
        if pk["picks"] <= 0 or not pk["choices"]:
            self.close_pack()
        return True, msg

    def close_pack(self):
        back = self.pack["back"] if self.pack else "shop"
        self.pack = None
        self.stage = back

    # ---- using tarots and planets ----
    def use_planet(self, name):
        hand = PLANETS[name]
        self.levels[hand] += 1
        for j in self.jokers:
            if j["k"] == "Constellation":
                j["st"]["v"] += 1
        self.last_used = name
        return f"{hand}: level {self.levels[hand]}"

    def _destroy(self, cards):
        ids = {c["id"] for c in cards}
        self.deck = [c for c in self.deck if c["id"] not in ids]
        if self.rnd:
            self.rnd.hand = [c for c in self.rnd.hand if c["id"] not in ids]

    def use_tarot(self, name, sel):
        """Use a tarot on the selected cards (in hand order). (ok, message)"""
        _e, lo, hi, _t = TAROTS[name]
        if lo and not lo <= len(sel) <= hi:
            return False, (f"Select {lo} card{'s' if lo > 1 else ''}" if lo == hi else f"Select {lo} to {hi} cards")
        room = self.cons_slots - len(self.consumables)
        msg = None
        if name in ENH_TAROT:
            for c in sel:
                c["enh"] = ENH_TAROT[name]
        elif name in SUIT_TAROT:
            for c in sel:
                c["s"] = SUIT_TAROT[name]
        elif name == "Strength":
            for c in sel:
                c["r"] = 2 if c["r"] == 14 else c["r"] + 1
        elif name == "The Hanged Man":
            self._destroy(sel)
        elif name == "Death":
            left, right = sel
            left.update({k: v for k, v in right.items() if k != "id"})
        elif name == "The Fool":
            if not self.last_used:
                return False, "Nothing to copy yet"
            if room <= 0:
                return False, "No room for a consumable"
            self.consumables.append({"k": self.last_used,
                                     "type": "planet" if self.last_used in PLANETS else "tarot"})
        elif name == "The High Priestess":
            if room <= 0:
                return False, "No room for a consumable"
            for _ in range(min(2, room)):
                self.consumables.append({"k": self.rng.choice(self.planet_pool()), "type": "planet"})
        elif name == "The Emperor":
            if room <= 0:
                return False, "No room for a consumable"
            for _ in range(min(2, room)):
                self.consumables.append({"k": self.rng.choice([t for t in TAROTS if t != "The Fool"]),
                                         "type": "tarot"})
        elif name == "The Hermit":
            gain = min(max(0, self.money), 20)
            self.money += gain
            msg = f"+${gain}"
        elif name == "Temperance":
            gain = min(50, sum(j["sell"] for j in self.jokers))
            self.money += gain
            msg = f"+${gain}"
        elif name == "The Wheel of Fortune":
            plain = [j for j in self.jokers if not j["ed"]]
            if not plain:
                return False, "No Joker to improve"
            if self.rng.random() < 0.25:
                j = self.rng.choice(plain)
                x = self.rng.random()
                j["ed"] = "foil" if x < 0.5 else "holo" if x < 0.85 else "poly"
                msg = f"{j['k']} is now {EDITIONS[j['ed']][0]}!"
            else:
                msg = "Nope!"
        elif name == "Judgement":
            if len(self.jokers) >= self.joker_slots:
                return False, "No room for a Joker"
            self.jokers.append(self.new_joker(self.random_joker_key(), self.roll_edition()))
        if name != "The Fool":
            self.last_used = name
        return True, msg

    def use_consumable(self, i, sel=()):
        c = self.consumables.pop(i)
        if c["type"] == "planet":
            return True, self.use_planet(c["k"])
        ok, msg = self.use_tarot(c["k"], list(sel))
        if not ok:
            self.consumables.insert(i, c)
        return ok, msg

    def most_played(self):
        h = max(self.played, key=lambda k: self.played[k])
        return h if self.played[h] else None
