"use strict";
// Claudeatro at the Gilded Joker (the fifteenth update): the Timeline's Claudeatro (ClaudeGames/claudeatro/game.py)
// ported whole - poker hands scored as chips times mult, Jokers, Tarot and Planet cards, the shop and its packs, the
// blinds and the antes - and, new here, the house: a wager of gold (or none), paid back a share for every blind beaten,
// and the unlocks kept with the village (decks by milestones, Jokers one for every blind ever beaten). A run is plain
// data, so it saves as JSON and is picked up again at the table. The window is 76e-casino.js; the house's rules are at
// the bottom of this file.
const CA_SUITS = "SHDC";
CM.CA = {
  SUITS: CA_SUITS, SYMBOL: { S: "♠", H: "♥", D: "♦", C: "♣" }, NAME: { S: "Spades", H: "Hearts", D: "Diamonds", C: "Clubs" }, FACE: [11, 12, 13],
  rankLabel: (r) => ({ 11: "J", 12: "Q", 13: "K", 14: "A" })[r] || String(r),
  rankChips: (r) => (r === 14 ? 11 : Math.min(10, r)),
  fmt: (n) => { n = Math.floor(n); return Math.abs(n) >= 1e11 ? n.toExponential(3).replace("e+", "e") : n.toLocaleString("en-GB"); },
  // name: base chips, base mult, chips per level, mult per level (best first)
  HANDS: [["Flush Five", 160, 16, 50, 3], ["Flush House", 140, 14, 40, 4], ["Five of a Kind", 120, 12, 35, 3], ["Straight Flush", 100, 8, 40, 4], ["Four of a Kind", 60, 7, 30, 3], ["Full House", 40, 4, 25, 2],
    ["Flush", 35, 4, 15, 2], ["Straight", 30, 4, 30, 3], ["Three of a Kind", 30, 3, 20, 2], ["Two Pair", 20, 2, 20, 1], ["Pair", 10, 2, 15, 1], ["High Card", 5, 1, 10, 1]],
  HIDDEN: ["Flush Five", "Flush House", "Five of a Kind"],
  PLANETS: { Pluto: "High Card", Mercury: "Pair", Uranus: "Two Pair", Venus: "Three of a Kind", Saturn: "Straight", Jupiter: "Flush", Earth: "Full House", Mars: "Four of a Kind", Neptune: "Straight Flush", "Planet X": "Five of a Kind", Ceres: "Flush House", Eris: "Flush Five" },
  ENHANCEMENTS: { bonus: ["Bonus Card", "+30 extra Chips"], mult: ["Mult Card", "+4 Mult"], wild: ["Wild Card", "Counts as every suit"], glass: ["Glass Card", "x2 Mult; 1 in 4 chance to break when scored"], steel: ["Steel Card", "x1.5 Mult while this card stays in hand"],
    stone: ["Stone Card", "+50 Chips; no rank or suit; always scores"], gold: ["Gold Card", "$3 if this card is held in hand at the end of the round"], lucky: ["Lucky Card", "1 in 5 chance for +20 Mult; 1 in 15 chance to win $20"] },
  EDITIONS: { foil: ["Foil", "+50 Chips"], holo: ["Holographic", "+10 Mult"], poly: ["Polychrome", "x1.5 Mult"] }, EDITION_COST: { foil: 2, holo: 3, poly: 5 },
  // name: [emoji, rarity (1 common, 2 uncommon, 3 rare), cost, what it does]
  JOKERS: {
    Joker: ["🃏", 1, 2, "+4 Mult"], "Greedy Joker": ["💎", 1, 5, "Played ♦ Diamonds give +3 Mult when scored"], "Lusty Joker": ["💋", 1, 5, "Played ♥ Hearts give +3 Mult when scored"], "Wrathful Joker": ["😤", 1, 5, "Played ♠ Spades give +3 Mult when scored"], "Gluttonous Joker": ["🍗", 1, 5, "Played ♣ Clubs give +3 Mult when scored"],
    "Jolly Joker": ["😀", 1, 3, "+8 Mult if the played hand contains a Pair"], "Zany Joker": ["🤪", 1, 4, "+12 Mult if the played hand contains a Three of a Kind"], "Mad Joker": ["😠", 1, 4, "+10 Mult if the played hand contains a Two Pair"], "Crazy Joker": ["🌀", 1, 4, "+12 Mult if the played hand contains a Straight"], "Droll Joker": ["😏", 1, 4, "+10 Mult if the played hand contains a Flush"],
    "Sly Joker": ["🦊", 1, 3, "+50 Chips if the played hand contains a Pair"], "Wily Joker": ["🐺", 1, 4, "+100 Chips if the played hand contains a Three of a Kind"], "Clever Joker": ["🦉", 1, 4, "+80 Chips if the played hand contains a Two Pair"], "Devious Joker": ["🐍", 1, 4, "+100 Chips if the played hand contains a Straight"], "Crafty Joker": ["🧶", 1, 4, "+80 Chips if the played hand contains a Flush"],
    "Half Joker": ["🌗", 1, 5, "+20 Mult if the played hand has 3 or fewer cards"], Banner: ["🚩", 1, 5, "+30 Chips for each remaining discard"], "Mystic Summit": ["🏔️", 1, 5, "+15 Mult when 0 discards remain"], Misprint: ["🖨️", 1, 4, "+0 to +23 Mult"], "Raised Fist": ["✊", 1, 5, "Adds double the rank of the lowest card held in hand to Mult"],
    "Scary Face": ["👹", 1, 4, "Played face cards give +30 Chips when scored"], "Smiley Face": ["😊", 1, 4, "Played face cards give +5 Mult when scored"], "Abstract Joker": ["🎨", 1, 4, "+3 Mult for each Joker you have"], "Gros Michel": ["🍌", 1, 5, "+15 Mult; 1 in 6 chance it's destroyed at the end of the round"],
    "Even Steven": ["👬", 1, 4, "Played 10s, 8s, 6s, 4s and 2s give +4 Mult when scored"], "Odd Todd": ["🎲", 1, 4, "Played Aces, 9s, 7s, 5s and 3s give +31 Chips when scored"], Scholar: ["🎓", 1, 4, "Played Aces give +20 Chips and +4 Mult when scored"], "Business Card": ["💼", 1, 4, "Played face cards have a 1 in 2 chance to give $2 when scored"],
    Supernova: ["💥", 1, 5, "Adds the number of times this poker hand has been played this run to Mult"], "Ride the Bus": ["🚌", 1, 6, "Gains +1 Mult per hand played in a row without a scoring face card"], "Blue Joker": ["🔵", 1, 5, "+2 Chips for each card remaining in your deck"], "Green Joker": ["🟢", 1, 4, "Gains +1 Mult per hand played; loses 1 Mult per discard"],
    "Ice Cream": ["🍦", 1, 5, "+100 Chips; -5 Chips for every hand played"], Popcorn: ["🍿", 1, 5, "+20 Mult; -4 Mult for every round played"], "Walkie Talkie": ["📻", 1, 4, "Played 10s and 4s give +10 Chips and +4 Mult when scored"], "Golden Joker": ["🪙", 1, 6, "Earn $4 at the end of the round"],
    Egg: ["🥚", 1, 4, "Gains $3 of sell value at the end of every round"], "Delayed Gratification": ["⏳", 1, 4, "Earn $2 per discard left if no discards were used this round"], Juggler: ["🤹", 1, 4, "+1 hand size"], Drunkard: ["🍺", 1, 4, "+1 discard every round"], "Credit Card": ["💳", 1, 1, "You can go up to $20 into debt"],
    "Chaos the Clown": ["🤡", 1, 4, "1 free reroll in every shop"], "Hanging Chad": ["🗳️", 1, 4, "Retrigger the first played card used in scoring"], Photograph: ["📷", 1, 5, "The first played face card gives x2 Mult when scored"], "Square Joker": ["🟥", 1, 4, "Gains +4 Chips whenever the played hand has exactly 4 cards"],
    Runner: ["🏃", 1, 5, "Gains +15 Chips whenever the played hand contains a Straight"], Splash: ["💦", 1, 3, "Every played card counts in scoring"], Cavendish: ["🍌", 1, 4, "x3 Mult; 1 in 1000 chance it's destroyed at the end of the round"],
    Hiker: ["🥾", 2, 5, "Every played card permanently gains +5 Chips when scored"], Fibonacci: ["🐚", 2, 8, "Played Aces, 2s, 3s, 5s and 8s give +8 Mult when scored"], "Four Fingers": ["✋", 2, 7, "Flushes and Straights can be made with 4 cards"], Shortcut: ["↗️", 2, 7, "Straights can skip a rank (like 10 8 6 5 3)"],
    Pareidolia: ["👁️", 2, 5, "Every card counts as a face card"], "Smeared Joker": ["🖌️", 2, 7, "♥ Hearts and ♦ Diamonds count as one suit, and so do ♠ Spades and ♣ Clubs"], Mime: ["🎭", 2, 5, "Retrigger the abilities of every card held in hand"], "Steel Joker": ["🔩", 2, 7, "x0.2 Mult for each Steel Card in your full deck"],
    Constellation: ["✨", 2, 6, "Gains x0.1 Mult every time a Planet card is used"], Hack: ["💻", 2, 6, "Retrigger every played 2, 3, 4 and 5"], Dusk: ["🌆", 2, 5, "Retrigger every played card in the final hand of the round"], "Sock and Buskin": ["🩰", 2, 6, "Retrigger every played face card"],
    Bootstraps: ["👢", 2, 7, "+2 Mult for every $5 you have"], Blackboard: ["⬛", 2, 6, "x3 Mult if every card held in hand is a ♠ Spade or ♣ Club"], Acrobat: ["🤸", 2, 6, "x3 Mult on the final hand of the round"], "Joker Stencil": ["🖼️", 2, 8, "x1 Mult for each empty Joker slot (Joker Stencil counts as empty)"],
    Rocket: ["🚀", 2, 6, "Earn $1 at the end of the round; the payout grows by $2 for each Boss Blind beaten"], "To the Moon": ["📈", 2, 5, "Earn an extra $1 of interest for every $5 you have at the end of the round"], Burglar: ["🦹", 2, 6, "When a Blind is selected, gain +3 hands and lose all discards"],
    "Shoot the Moon": ["🌕", 2, 5, "Every Queen held in hand gives +13 Mult"], "Cloud 9": ["☁️", 2, 7, "Earn $1 for each 9 in your full deck at the end of the round"], "Rough Gem": ["💠", 2, 7, "Played ♦ Diamonds earn $1 when scored"], Bull: ["🐂", 2, 6, "+2 Chips for each $1 you have"],
    Baron: ["🎩", 3, 8, "Every King held in hand gives x1.5 Mult"], "The Duo": ["👯", 3, 8, "x2 Mult if the played hand contains a Pair"], "The Trio": ["🎺", 3, 8, "x3 Mult if the played hand contains a Three of a Kind"], "The Family": ["🏠", 3, 8, "x4 Mult if the played hand contains a Four of a Kind"],
    "The Order": ["📏", 3, 8, "x3 Mult if the played hand contains a Straight"], "The Tribe": ["🏕️", 3, 8, "x2 Mult if the played hand contains a Flush"], Blueprint: ["📘", 3, 10, "Copies the ability of the Joker to its right"],
  },
  JOKER_START: { "Ice Cream": 100, Popcorn: 20, Rocket: 1 },
  SUIT_JOKERS: { "Greedy Joker": "D", "Lusty Joker": "H", "Wrathful Joker": "S", "Gluttonous Joker": "C" },
  TYPE_MULT: { "Jolly Joker": ["Pair", 8], "Zany Joker": ["Three of a Kind", 12], "Mad Joker": ["Two Pair", 10], "Crazy Joker": ["Straight", 12], "Droll Joker": ["Flush", 10] },
  TYPE_CHIPS: { "Sly Joker": ["Pair", 50], "Wily Joker": ["Three of a Kind", 100], "Clever Joker": ["Two Pair", 80], "Devious Joker": ["Straight", 100], "Crafty Joker": ["Flush", 80] },
  TYPE_X: { "The Duo": ["Pair", 2], "The Trio": ["Three of a Kind", 3], "The Family": ["Four of a Kind", 4], "The Order": ["Straight", 3], "The Tribe": ["Flush", 2] },
  // name: [emoji, fewest cards to select, most, what it does]
  TAROTS: {
    "The Fool": ["🎒", 0, 0, "Creates a copy of the last Tarot or Planet card used (not The Fool)"], "The Magician": ["🪄", 1, 2, "Turns up to 2 selected cards into Lucky Cards"], "The High Priestess": ["📿", 0, 0, "Creates up to 2 random Planet cards"], "The Empress": ["👑", 1, 2, "Turns up to 2 selected cards into Mult Cards"],
    "The Emperor": ["🤴", 0, 0, "Creates up to 2 random Tarot cards"], "The Hierophant": ["⛪", 1, 2, "Turns up to 2 selected cards into Bonus Cards"], "The Lovers": ["💞", 1, 1, "Turns 1 selected card into a Wild Card"], "The Chariot": ["🛞", 1, 1, "Turns 1 selected card into a Steel Card"],
    Justice: ["⚖️", 1, 1, "Turns 1 selected card into a Glass Card"], "The Hermit": ["🏮", 0, 0, "Doubles your money (max +$20)"], "The Wheel of Fortune": ["🎡", 0, 0, "1 in 4 chance to give a random Joker Foil, Holographic or Polychrome"], Strength: ["💪", 1, 2, "Raises the rank of up to 2 selected cards by 1"],
    "The Hanged Man": ["🙃", 1, 2, "Destroys up to 2 selected cards"], Death: ["💀", 2, 2, "Select 2 cards: the left one becomes a copy of the right one"], Temperance: ["🍷", 0, 0, "Gives the total sell value of your Jokers (max $50)"], "The Devil": ["👿", 1, 1, "Turns 1 selected card into a Gold Card"],
    "The Tower": ["🗼", 1, 1, "Turns 1 selected card into a Stone Card"], "The Star": ["⭐", 1, 3, "Turns up to 3 selected cards into ♦ Diamonds"], "The Moon": ["🌙", 1, 3, "Turns up to 3 selected cards into ♣ Clubs"], "The Sun": ["☀️", 1, 3, "Turns up to 3 selected cards into ♥ Hearts"],
    Judgement: ["📯", 0, 0, "Creates a random Joker"], "The World": ["🌍", 1, 3, "Turns up to 3 selected cards into ♠ Spades"],
  },
  ENH_TAROT: { "The Magician": "lucky", "The Empress": "mult", "The Hierophant": "bonus", "The Lovers": "wild", "The Chariot": "steel", Justice: "glass", "The Devil": "gold", "The Tower": "stone" },
  SUIT_TAROT: { "The Star": "D", "The Moon": "C", "The Sun": "H", "The World": "S" },
  // name: [colour, size times the ante's base, first ante, what it does]
  BOSSES: {
    "The Hook": ["#A84024", 2, 1, "Discards 2 random cards held in hand after every hand played"], "The Club": ["#8FA35A", 2, 1, "All ♣ Club cards are debuffed"], "The Goad": ["#B95B9B", 2, 1, "All ♠ Spade cards are debuffed"], "The Head": ["#9C88AE", 2, 1, "All ♥ Heart cards are debuffed"],
    "The Window": ["#9A9283", 2, 1, "All ♦ Diamond cards are debuffed"], "The Psychic": ["#D9A82C", 2, 1, "Hands must have 5 cards"], "The Manacle": ["#575757", 2, 1, "-1 hand size"], "The Wall": ["#8A59A5", 4, 2, "Extra large blind"], "The Water": ["#5FA3BF", 2, 2, "Start with 0 discards"],
    "The Arm": ["#6865F3", 2, 2, "Lowers the level of each poker hand you play"], "The Flint": ["#E56A2F", 2, 2, "Base Chips and Mult are halved"], "The Needle": ["#5C6E31", 1, 2, "Play only 1 hand"], "The Mouth": ["#AE718E", 2, 2, "Play only 1 kind of poker hand this round"],
    "The Eye": ["#4B71E4", 2, 3, "No repeated poker hands this round"], "The Tooth": ["#B52D2D", 2, 3, "Lose $1 for every card played"], "The Plant": ["#709284", 2, 4, "All face cards are debuffed"], "The Serpent": ["#439A4F", 2, 5, "After every play or discard, always draw 3 cards"], "The Ox": ["#B95C08", 2, 6, "Playing your most played poker hand sets your money to $0"],
  },
  SHOWDOWN: { "Violet Vessel": ["#8A71E1", 6, 8, "Very large blind"], "Verdant Leaf": ["#56A786", 2, 8, "All cards are debuffed until you sell a Joker"], "Crimson Heart": ["#AC3232", 2, 8, "One random Joker is disabled every hand"] },
  SUIT_BOSS: { "The Club": "C", "The Goad": "S", "The Head": "H", "The Window": "D" },
  TAGS: {
    "Uncommon Tag": ["🟩", "The next shop has a free Uncommon Joker"], "Rare Tag": ["🟥", "The next shop has a free Rare Joker"], "Investment Tag": ["📈", "Gain $25 after beating the next Boss Blind"], "Economy Tag": ["💰", "Doubles your money (max +$40)"],
    "Charm Tag": ["🔮", "Opens a free Mega Arcana Pack"], "Meteor Tag": ["☄️", "Opens a free Mega Celestial Pack"], "Buffoon Tag": ["🤡", "Opens a free Mega Buffoon Pack"], "Standard Tag": ["🂡", "Opens a free Mega Standard Pack"], "Handy Tag": ["🤚", "Gives $1 for every hand played this run"],
    "Garbage Tag": ["🗑️", "Gives $1 for every unused discard this run"], "Juggle Tag": ["🤹", "+3 hand size next round"], "Coupon Tag": ["🎟️", "Cards and packs in the next shop are free"], "D6 Tag": ["🎲", "Rerolls in the next shop start at $0"], "Speed Tag": ["⏩", "Gives $5 for every Blind you've skipped this run"],
  },
  PACK_TAGS: { "Charm Tag": "Arcana", "Meteor Tag": "Celestial", "Buffoon Tag": "Buffoon", "Standard Tag": "Standard" },
  VOUCHERS: { Overstock: ["📦", "+1 card slot in the shop"], "Clearance Sale": ["🏷️", "Everything in the shop is 25% off"], "Reroll Surplus": ["🔁", "Rerolls cost $2 less"], "Crystal Ball": ["🔮", "+1 consumable slot"], Grabber: ["🖐️", "+1 hand every round"], Wasteful: ["🗑️", "+1 discard every round"],
    "Tarot Merchant": ["🃏", "Tarot cards turn up twice as often in the shop"], "Planet Merchant": ["🪐", "Planet cards turn up twice as often in the shop"], "Seed Money": ["🌱", "Interest can reach $10 a round"], "Paint Brush": ["🖌️", "+1 hand size"], Antimatter: ["⚛️", "+1 Joker slot"], Blank: ["⬜", "Does nothing?"] },
  DECKS: { "Red Deck": ["#D9473C", "+1 discard every round"], "Blue Deck": ["#2F78C4", "+1 hand every round"], "Yellow Deck": ["#E3B23C", "Start with an extra $10"], "Green Deck": ["#3C9E5C", "At the end of each round, $2 per hand and $1 per discard left; no interest"],
    "Black Deck": ["#2B2B33", "+1 Joker slot; -1 hand every round"], "Abandoned Deck": ["#6E7F6A", "No face cards in your deck"], "Checkered Deck": ["#B03A54", "26 ♠ Spades and 26 ♥ Hearts"], "Erratic Deck": ["#8A5CC2", "Every card's rank and suit is random"] },
  PACKS: { Arcana: ["🔮", "#7A4FA8", "Tarot cards, used straight away"], Celestial: ["🌌", "#2C5A9E", "Planet cards, used straight away"], Buffoon: ["🤡", "#C2453B", "Jokers"], Standard: ["🂡", "#4F6E80", "playing cards to add to your deck"] },
  PACK_SIZES: { normal: ["", 4, 3, 1], jumbo: ["Jumbo ", 6, 5, 1], mega: ["Mega ", 8, 5, 2] },
  PACK_WEIGHTS: [["Arcana", "normal", 4], ["Arcana", "jumbo", 2], ["Arcana", "mega", 0.5], ["Celestial", "normal", 4], ["Celestial", "jumbo", 2], ["Celestial", "mega", 0.5], ["Buffoon", "normal", 1.2], ["Buffoon", "jumbo", 0.6], ["Buffoon", "mega", 0.15], ["Standard", "normal", 4], ["Standard", "jumbo", 2], ["Standard", "mega", 0.5]],
  ANTE_BASE: [300, 800, 2000, 5000, 11000, 20000, 35000, 50000], ANTE_LATE: [110000, 560000, 7200000, 300000000],
};
const CA = CM.CA;
CA.HAND_INFO = {}; for (const h of CA.HANDS) CA.HAND_INFO[h[0]] = h.slice(1);
CA.anteBase = (a) => (a <= 8 ? CA.ANTE_BASE[Math.max(1, a) - 1] : a - 9 < CA.ANTE_LATE.length ? CA.ANTE_LATE[a - 9] : CA.ANTE_LATE[CA.ANTE_LATE.length - 1] * 40 ** (a - 12));
CA.packName = (kind, size) => `${CA.PACK_SIZES[size][0]}${kind} Pack`;

// ---- a run: the deck, the Jokers, the money, the antes, and what is happening now (stage) ----
CM.CaRun = class {
  constructor(deck = "Red Deck", seed = 1, pool = null) {
    this.seed = seed >>> 0; this.rngS = new CM.Random(this.seed).s; this.deckName = deck; this.nextId = 1; this.pool = pool;   // (pool: the Jokers unlocked, or every one)
    this.money = 4 + (deck === "Yellow Deck" ? 10 : 0); this.ante = 1; this.blind = 0; this.roundNo = 1;
    this.handsBase = 4 + (deck === "Blue Deck" ? 1 : 0) - (deck === "Black Deck" ? 1 : 0); this.discardsBase = 3 + (deck === "Red Deck" ? 1 : 0); this.handSizeBase = 8;
    this.jokerSlots = 5 + (deck === "Black Deck" ? 1 : 0); this.consSlots = 2; this.shopSlots = 2;
    this.jokers = []; this.consumables = []; this.vouchers = []; this.pendingTags = [];
    this.levels = {}; this.played = {}; for (const h of CA.HANDS) { this.levels[h[0]] = 1; this.played[h[0]] = 0; }
    this.seenBosses = []; this.boss = null; this.skipTags = []; this.voucherOffer = null; this.blindState = ["", "", ""]; this.shop = null; this.pack = null; this.cash = []; this.notes = [];
    this.stage = "blind"; this.lastWasBoss = false; this.won = false; this.endless = false; this.juggle = 0; this.lastUsed = null; this.extinct = false;
    this.handsTotal = 0; this.discardsUnused = 0; this.skips = 0; this.bestHand = 0; this.rnd = null;
    this.deck = this.makeDeck(deck);
    this.newAnte();
  }
  static fromJSON(d) { const r = Object.create(CM.CaRun.prototype); Object.assign(r, JSON.parse(JSON.stringify(d))); if (r.rnd) { const byId = {}; for (const c of r.deck) byId[c.id] = c; for (const k of ["draw", "hand", "discard", "played"]) r.rnd[k] = r.rnd[k].map((i) => byId[i]).filter(Boolean); } return r; }
  toJSON() { const d = Object.assign({}, this); delete d.__src; if (this.rnd) { d.rnd = Object.assign({}, this.rnd); for (const k of ["draw", "hand", "discard", "played"]) d.rnd[k] = this.rnd[k].map((c) => c.id); } return d; }
  // the run's dice, kept as a number so a save picks them up where they were
  get rng() { const R = new CM.Random(1); R.s = this.rngS; const self = this; return { next: () => { const v = R.next(); self.rngS = R.s; return v; } }; }
  rand() { return this.rng.next(); }
  randint(a, b) { return a + Math.floor(this.rand() * (b - a + 1)); }
  choice(list) { return list[Math.floor(this.rand() * list.length)]; }
  shuffle(list) { for (let i = list.length - 1; i > 0; i--) { const j = Math.floor(this.rand() * (i + 1)); [list[i], list[j]] = [list[j], list[i]]; } return list; }
  sample(list, n) { return this.shuffle(list.slice()).slice(0, n); }
  // ---- cards ----
  newCard(r, s, enh = null, ed = null) { return { r, s, enh, ed, bonus: 0, id: this.nextId++ }; }
  makeDeck(name) {
    const out = [];
    for (const s of CA_SUITS) for (let r = 2; r <= 14; r++) {
      if (name === "Abandoned Deck" && CA.FACE.includes(r)) continue;
      let ss = s, rr = r;
      if (name === "Checkered Deck") ss = "SC".includes(s) ? "S" : "H"; else if (name === "Erratic Deck") { rr = this.randint(2, 14); ss = this.choice(CA_SUITS); }
      out.push(this.newCard(rr, ss));
    }
    return out;
  }
  randomCard() { const c = this.newCard(this.randint(2, 14), this.choice(CA_SUITS)); if (this.rand() < 0.4) c.enh = this.choice(Object.keys(CA.ENHANCEMENTS)); const x = this.rand(); c.ed = x < 0.012 ? "poly" : x < 0.04 ? "holo" : x < 0.08 ? "foil" : null; return c; }
  has(k) { return this.jokers.some((j) => j.k === k); }
  count(k) { return this.jokers.filter((j) => j.k === k).length; }
  suitIs(c, s) { if (c.enh === "stone") return false; if (c.enh === "wild") return true; if (this.has("Smeared Joker")) return "HD".includes(c.s) === "HD".includes(s); return c.s === s; }
  isFace(c) { return c.enh !== "stone" && (CA.FACE.includes(c.r) || this.has("Pareidolia")); }
  debuffed(c) { const r = this.rnd; if (!r || !r.boss) return false; if (r.boss === "Verdant Leaf" && r.leaf) return true; if (CA.SUIT_BOSS[r.boss] && this.suitIs(c, CA.SUIT_BOSS[r.boss])) return true; return r.boss === "The Plant" && this.isFace(c); }
  // ---- Jokers, Tarots, Planets ----
  newJoker(key, ed = null) { const cost = CA.JOKERS[key][2] + (CA.EDITION_COST[ed] || 0); return { k: key, ed, st: { v: CA.JOKER_START[key] || 0 }, id: this.nextId++, sell: Math.max(1, Math.floor(cost / 2)) }; }
  jokerAllowed(k) { if (this.pool && !this.pool.includes(k)) return false; if (k === "Cavendish") return this.extinct; if (k === "Gros Michel") return !this.extinct; return true; }
  randomJokerKey(rarity = null, exclude = []) {
    if (rarity === null) { const x = this.rand(); rarity = x < 0.7 ? 1 : x < 0.95 ? 2 : 3; }
    const owned = new Set(this.jokers.map((j) => j.k).concat([...exclude]));
    let pool = Object.keys(CA.JOKERS).filter((k) => CA.JOKERS[k][1] === rarity && !owned.has(k) && this.jokerAllowed(k));
    if (!pool.length) pool = Object.keys(CA.JOKERS).filter((k) => CA.JOKERS[k][1] === rarity && this.jokerAllowed(k));
    if (!pool.length) pool = Object.keys(CA.JOKERS).filter((k) => this.jokerAllowed(k) && !owned.has(k));   // (nothing of that rarity unlocked yet: any that is)
    if (!pool.length) pool = ["Joker"];
    return this.choice(pool);
  }
  rollEdition() { const x = this.rand(); return x < 0.003 ? "poly" : x < 0.017 ? "holo" : x < 0.037 ? "foil" : null; }
  planetPool() { return Object.keys(CA.PLANETS).filter((p) => !CA.HIDDEN.includes(CA.PLANETS[p]) || this.played[CA.PLANETS[p]] > 0); }
  nines() { return this.deck.filter((c) => c.r === 9 && c.enh !== "stone").length; }
  jokerStatus(j) {
    const k = j.k, v = j.st.v || 0, r = this.rnd;
    if (["Ride the Bus", "Green Joker", "Popcorn"].includes(k)) return `Currently +${v} Mult`;
    if (["Ice Cream", "Square Joker", "Runner"].includes(k)) return `Currently +${v} Chips`;
    if (k === "Constellation") return `Currently x${(1 + 0.1 * v).toFixed(1)} Mult`;
    if (k === "Rocket") return `Currently $${v}`;
    if (k === "Abstract Joker") return `Currently +${3 * this.jokers.length} Mult`;
    if (k === "Blue Joker") return `Currently +${2 * (r ? r.draw.length : this.deck.length)} Chips`;
    if (k === "Bull") return `Currently +${2 * Math.max(0, this.money)} Chips`;
    if (k === "Bootstraps") return `Currently +${2 * Math.max(0, Math.floor(this.money / 5))} Mult`;
    if (k === "Steel Joker") return `Currently x${(1 + 0.2 * this.deck.filter((c) => c.enh === "steel").length).toFixed(1)} Mult`;
    if (k === "Joker Stencil") return `Currently x${this.jokerSlots - this.jokers.length + this.count("Joker Stencil")} Mult`;
    if (k === "Cloud 9") return `Currently $${this.nines()}`;
    return null;
  }
  // ---- antes and blinds ----
  newAnte() {
    let pool;
    if (this.ante % 8 === 0) pool = Object.keys(CA.SHOWDOWN);
    else { pool = Object.keys(CA.BOSSES).filter((b) => CA.BOSSES[b][2] <= this.ante && !this.seenBosses.includes(b)); if (!pool.length) { this.seenBosses = []; pool = Object.keys(CA.BOSSES).filter((b) => CA.BOSSES[b][2] <= this.ante); } }
    this.boss = this.choice(pool); this.seenBosses.push(this.boss);
    this.skipTags = [this.choice(Object.keys(CA.TAGS)), this.choice(Object.keys(CA.TAGS))];
    const left = Object.keys(CA.VOUCHERS).filter((v) => !this.vouchers.includes(v)); this.voucherOffer = left.length ? this.choice(left) : null;
    this.blindState = ["", "", ""];
  }
  bossInfo(name) { name = name || this.boss; return CA.BOSSES[name] || CA.SHOWDOWN[name]; }
  blinds() {
    const base = CA.anteBase(this.ante), [colour, size, , text] = this.bossInfo();
    return [{ kind: "small", name: "Small Blind", target: base, reward: 3, colour: "#2E6DA4", text: "" }, { kind: "big", name: "Big Blind", target: Math.floor(base * 1.5), reward: 4, colour: "#D08B1A", text: "" },
      { kind: "boss", name: this.boss, target: Math.floor(base * size), reward: CA.SHOWDOWN[this.boss] ? 8 : 5, colour, text }];
  }
  selectBlind() {
    const b = this.blinds()[this.blind], boss = b.kind === "boss" ? b.name : null;
    const r = { kind: b.kind, name: b.name, target: b.target, reward: b.reward, boss, score: 0, hands: this.handsBase + (this.vouchers.includes("Grabber") ? 1 : 0),
      discards: this.discardsBase + (this.vouchers.includes("Wasteful") ? 1 : 0) + this.count("Drunkard"), handSize: this.handSizeBase + (this.vouchers.includes("Paint Brush") ? 1 : 0) + this.count("Juggler") + this.juggle,
      draw: this.deck.slice(), hand: [], discard: [], played: [], usedTypes: [], discardsUsed: 0, handsPlayed: 0, leaf: boss === "Verdant Leaf", disabled: null, broken: [], sort: "rank", ox: null };
    this.juggle = 0;
    if (this.has("Burglar")) { r.hands += 3 * this.count("Burglar"); r.discards = 0; }
    if (boss === "The Water") r.discards = 0;
    if (boss === "The Needle") r.hands = 1;
    if (boss === "The Manacle") r.handSize -= 1;
    if (boss === "The Ox" && Math.max(...Object.values(this.played)) > 0) r.ox = Object.keys(this.played).reduce((a, h) => (this.played[h] > this.played[a] ? h : a));
    this.shuffle(r.draw); this.rnd = r; this.stage = "round"; this.drawUp(); this.crimson();
  }
  skipBlind() { const tag = this.skipTags[this.blind]; this.blindState[this.blind] = "skipped"; this.blind += 1; this.skips += 1; return this.applyTag(tag); }
  applyTag(tag) {
    let gain = null;
    if (tag === "Economy Tag") gain = Math.min(Math.max(0, this.money), 40); else if (tag === "Handy Tag") gain = this.handsTotal; else if (tag === "Garbage Tag") gain = this.discardsUnused; else if (tag === "Speed Tag") gain = 5 * this.skips;
    if (gain !== null) { this.money += gain; return `${tag}: +$${gain}`; }
    if (tag === "Juggle Tag") { this.juggle += 3; return "Juggle Tag: +3 hand size next round"; }
    if (CA.PACK_TAGS[tag]) { this.openPack(CA.PACK_TAGS[tag], "mega", this.stage); return null; }
    this.pendingTags.push(tag); return `${tag}: ${CA.TAGS[tag][1].toLowerCase()}`;
  }
  crimson() { const r = this.rnd; if (r && r.boss === "Crimson Heart") r.disabled = this.jokers.length ? this.choice(this.jokers).id : null; }
  // ---- the hand ----
  sortHand(mode) {
    const r = this.rnd; if (mode) r.sort = mode; const order = { S: 0, H: 1, D: 2, C: 3 }, rank = (c) => (c.enh === "stone" ? 0 : c.r);
    if (r.sort === "rank") r.hand.sort((a, b) => rank(b) - rank(a) || order[a.s] - order[b.s]); else if (r.sort === "suit") r.hand.sort((a, b) => order[a.s] - order[b.s] || rank(b) - rank(a));
  }
  drawUp(n) { const r = this.rnd; n = n === undefined ? r.handSize - r.hand.length : n; for (let i = 0; i < Math.max(0, n); i++) { if (!r.draw.length) break; r.hand.push(r.draw.pop()); } this.sortHand(); }
  straight(cards, need) {
    const gap = this.has("Shortcut") ? 2 : 1, byRank = {}; for (const c of cards) if (!(c.r in byRank)) byRank[c.r] = c;
    let ranks = Object.keys(byRank).map(Number).sort((a, b) => a - b); if (byRank[14]) ranks = [1].concat(ranks);
    let best = [], cur = []; for (const r of ranks) { cur = cur.length && r - cur[cur.length - 1] <= gap ? cur.concat([r]) : [r]; if (cur.length > best.length) best = cur.slice(); }
    return best.length >= need ? best.map((r) => byRank[r === 1 ? 14 : r]) : [];
  }
  // (poker hand, the cards that score, every poker hand it contains)
  evaluate(cards) {
    const ranked = cards.filter((c) => c.enh !== "stone"), need = this.has("Four Fingers") ? 4 : 5, groups = {};
    for (const c of ranked) (groups[c.r] = groups[c.r] || []).push(c);
    const big = Object.values(groups).sort((a, b) => b.length - a.length || b[0].r - a[0].r), sizes = big.map((g) => g.length).concat([0, 0]);
    let flush = []; if (ranked.length >= need) for (const s of CA_SUITS) { const fs = ranked.filter((c) => this.suitIs(c, s)); if (fs.length >= need && fs.length > flush.length) flush = fs; }
    const straight = this.straight(ranked, need), full = sizes[0] >= 3 && sizes[1] >= 2, contains = new Set();
    if (sizes[0] >= 2) contains.add("Pair"); if (sizes[1] >= 2) contains.add("Two Pair"); if (sizes[0] >= 3) contains.add("Three of a Kind"); if (sizes[0] >= 4) contains.add("Four of a Kind");
    if (straight.length) contains.add("Straight"); if (flush.length) contains.add("Flush"); if (full) contains.add("Full House"); if (straight.length && flush.length) contains.add("Straight Flush");
    let name, sc;
    if (sizes[0] >= 5 && flush.length) [name, sc] = ["Flush Five", ranked];
    else if (full && flush.length) [name, sc] = ["Flush House", ranked];
    else if (sizes[0] >= 5) [name, sc] = ["Five of a Kind", big[0]];
    else if (straight.length && flush.length) [name, sc] = ["Straight Flush", straight.concat(flush.filter((c) => !straight.includes(c)))];
    else if (sizes[0] >= 4) [name, sc] = ["Four of a Kind", big[0]];
    else if (full) [name, sc] = ["Full House", big[0].concat(big[1])];
    else if (flush.length) [name, sc] = ["Flush", flush];
    else if (straight.length) [name, sc] = ["Straight", straight];
    else if (sizes[0] >= 3) [name, sc] = ["Three of a Kind", big[0]];
    else if (sizes[1] >= 2) [name, sc] = ["Two Pair", big[0].concat(big[1])];
    else if (sizes[0] >= 2) [name, sc] = ["Pair", big[0]];
    else [name, sc] = ["High Card", ranked.length ? [ranked.reduce((a, c) => (c.r > a.r ? c : a))] : []];
    contains.add(name);
    const ids = new Set(sc.map((c) => c.id)), scoring = this.has("Splash") ? cards.slice() : cards.filter((c) => ids.has(c.id) || c.enh === "stone");
    return [name, scoring, contains];
  }
  handValue(name) { const [chips, mult, lc, lm] = CA.HAND_INFO[name], lv = this.levels[name]; return [chips + lc * (lv - 1), mult + lm * (lv - 1)]; }
  preview(cards) { if (!cards.length) return null; const name = this.evaluate(cards)[0]; let [chips, mult] = this.handValue(name); if (this.rnd && this.rnd.boss === "The Flint") { chips = Math.floor((chips + 1) / 2); mult = Math.floor((mult + 1) / 2); } return [name, this.levels[name], chips, mult]; }
  // ---- scoring ----
  active() {
    const out = [], r = this.rnd;
    this.jokers.forEach((j, i) => { if (j.dead || (r && r.disabled === j.id)) return; let src = j, k = i; while (src && src.k === "Blueprint") { k += 1; src = this.jokers[k] || null; } out.push([i, src ? src.k : null, src]); });
    return out;
  }
  onCard(key, c, firstFace) {
    const r = c.enh === "stone" ? null : c.r;
    if (CA.SUIT_JOKERS[key]) return this.suitIs(c, CA.SUIT_JOKERS[key]) ? [["mult", 3]] : [];
    if (key === "Fibonacci" && [14, 2, 3, 5, 8].includes(r)) return [["mult", 8]];
    if (key === "Scary Face" && this.isFace(c)) return [["chips", 30]];
    if (key === "Smiley Face" && this.isFace(c)) return [["mult", 5]];
    if (key === "Even Steven" && [2, 4, 6, 8, 10].includes(r)) return [["mult", 4]];
    if (key === "Odd Todd" && [14, 3, 5, 7, 9].includes(r)) return [["chips", 31]];
    if (key === "Scholar" && r === 14) return [["chips", 20], ["mult", 4]];
    if (key === "Walkie Talkie" && [10, 4].includes(r)) return [["chips", 10], ["mult", 4]];
    if (key === "Photograph" && firstFace !== null && c.id === firstFace) return [["xmult", 2]];
    if (key === "Business Card" && this.isFace(c) && this.rand() < 0.5) return [["money", 2]];
    if (key === "Rough Gem" && this.suitIs(c, "D")) return [["money", 1]];
    if (key === "Hiker") { c.bonus += 5; return [["info", "Upgrade!"]]; }
    return [];
  }
  independent(key, src, name, contains, cards) {
    const r = this.rnd, v = src ? src.st.v || 0 : 0;
    if (key === "Joker") return [["mult", 4]];
    if (CA.TYPE_MULT[key]) { const [h, n] = CA.TYPE_MULT[key]; return contains.has(h) ? [["mult", n]] : []; }
    if (CA.TYPE_CHIPS[key]) { const [h, n] = CA.TYPE_CHIPS[key]; return contains.has(h) ? [["chips", n]] : []; }
    if (CA.TYPE_X[key]) { const [h, n] = CA.TYPE_X[key]; return contains.has(h) ? [["xmult", n]] : []; }
    if (key === "Half Joker") return cards.length <= 3 ? [["mult", 20]] : [];
    if (key === "Banner") return r.discards > 0 ? [["chips", 30 * r.discards]] : [];
    if (key === "Mystic Summit") return r.discards === 0 ? [["mult", 15]] : [];
    if (key === "Misprint") return [["mult", this.randint(0, 23)]];
    if (key === "Abstract Joker") return [["mult", 3 * this.jokers.length]];
    if (key === "Gros Michel") return [["mult", 15]];
    if (key === "Cavendish") return [["xmult", 3]];
    if (key === "Supernova") return [["mult", this.played[name]]];
    if (["Ride the Bus", "Green Joker", "Popcorn"].includes(key)) return v > 0 ? [["mult", v]] : [];
    if (["Ice Cream", "Square Joker", "Runner"].includes(key)) return v > 0 ? [["chips", v]] : [];
    if (key === "Blue Joker") return r.draw.length ? [["chips", 2 * r.draw.length]] : [];
    if (key === "Bull") return this.money > 0 ? [["chips", 2 * this.money]] : [];
    if (key === "Bootstraps") return this.money >= 5 ? [["mult", 2 * Math.floor(this.money / 5)]] : [];
    if (key === "Steel Joker") { const n = this.deck.filter((c) => c.enh === "steel").length; return n ? [["xmult", Math.round((1 + 0.2 * n) * 100) / 100]] : []; }
    if (key === "Constellation") return v ? [["xmult", Math.round((1 + 0.1 * v) * 100) / 100]] : [];
    if (key === "Blackboard") return r.hand.every((c) => this.suitIs(c, "S") || this.suitIs(c, "C")) ? [["xmult", 3]] : [];
    if (key === "Acrobat") return r.hands === 0 ? [["xmult", 3]] : [];
    if (key === "Joker Stencil") { const x = this.jokerSlots - this.jokers.length + this.count("Joker Stencil"); return x > 1 ? [["xmult", x]] : []; }
    return [];
  }
  // play the cards at these hand positions: what happened, step by step, for the window to show; then afterPlay()
  play(idx) {
    const r = this.rnd; idx = [...new Set(idx)].sort((a, b) => a - b);
    if (!r || idx.length < 1 || idx.length > 5 || r.hands <= 0 || r.played.length) return null;
    const cards = idx.map((i) => r.hand[i]), ids = new Set(cards.map((c) => c.id));
    r.hand = r.hand.filter((c) => !ids.has(c.id)); r.played = cards; r.hands -= 1; r.handsPlayed += 1; this.handsTotal += 1;
    const [name, scoring, contains] = this.evaluate(cards), boss = r.boss;
    const blocked = (boss === "The Psychic" && cards.length < 5) || (boss === "The Eye" && r.usedTypes.includes(name)) || (boss === "The Mouth" && r.usedTypes.length && name !== r.usedTypes[0]);
    if (!r.usedTypes.includes(name)) r.usedTypes.push(name);
    const t = { chips: 0, mult: 0, events: [] }, apply = (at, kind, v) => {
      let text;
      if (kind === "chips") { t.chips += v; text = `+${v}`; } else if (kind === "mult") { t.mult += v; text = `+${v} Mult`; } else if (kind === "xmult") { t.mult *= v; text = `x${v} Mult`; }
      else if (kind === "money") { this.money += v; text = v >= 0 ? `+$${v}` : `-$${-v}`; } else text = v;
      t.events.push({ at, text, kind, chips: t.chips, mult: t.mult });
    };
    if (boss === "The Tooth") apply(["hand"], "money", -cards.length);
    if (boss === "The Ox" && name === r.ox) { this.money = 0; apply(["hand"], "info", "$0!"); }
    this.played[name] += 1;
    if (boss === "The Arm" && this.levels[name] > 1) { this.levels[name] -= 1; apply(["hand"], "info", "Level down!"); }
    let [chips, mult] = this.handValue(name); if (boss === "The Flint") { chips = Math.floor((chips + 1) / 2); mult = Math.floor((mult + 1) / 2); }
    t.chips = chips; t.mult = mult;
    const res = { hand: name, level: this.levels[name], base: [chips, mult], scoring: scoring.map((c) => c.id) };
    let total;
    if (blocked) { apply(["hand"], "info", "Not allowed!"); total = 0; } else total = this.score(t, apply, name, cards, scoring, contains);
    r.score += total; this.bestHand = Math.max(this.bestHand, total);
    res.events = t.events; res.total = total;
    return res;
  }
  score(t, apply, name, cards, scoring, contains) {
    const r = this.rnd, active = this.active(), pos = {}; cards.forEach((c, i) => { pos[c.id] = i; });
    const live = scoring.filter((c) => !this.debuffed(c));
    this.jokers.forEach((j, i) => {                                       // the Jokers that grow as you play
      const k = j.k;
      if (k === "Ride the Bus") { if (live.some((c) => this.isFace(c))) { if (j.st.v) { j.st.v = 0; apply(["joker", i], "info", "Reset"); } } else { j.st.v += 1; apply(["joker", i], "info", "Upgrade!"); } }
      else if (k === "Green Joker") { j.st.v += 1; apply(["joker", i], "info", "+1 Mult"); }
      else if (k === "Square Joker" && cards.length === 4) { j.st.v += 4; apply(["joker", i], "info", "Upgrade!"); }
      else if (k === "Runner" && contains.has("Straight")) { j.st.v += 15; apply(["joker", i], "info", "Upgrade!"); }
    });
    const firstFaceCard = live.find((c) => this.isFace(c)), firstFace = firstFaceCard ? firstFaceCard.id : null, final = r.hands === 0;
    scoring.forEach((c, n) => {
      const at = ["played", pos[c.id]];
      if (this.debuffed(c)) { apply(at, "info", "Debuffed"); return; }
      const again = []; for (const [i, key] of active) if ((key === "Hanging Chad" && n === 0) || (key === "Sock and Buskin" && this.isFace(c)) || (key === "Hack" && c.enh !== "stone" && [2, 3, 4, 5].includes(c.r)) || (key === "Dusk" && final)) again.push(i);
      for (let rep = 0; rep <= again.length; rep++) {
        if (rep) apply(["joker", again[rep - 1]], "info", "Again!");
        if (c.enh === "stone") apply(at, "chips", 50 + c.bonus); else apply(at, "chips", CA.rankChips(c.r) + c.bonus + (c.enh === "bonus" ? 30 : 0));
        if (c.enh === "mult") apply(at, "mult", 4); else if (c.enh === "glass") apply(at, "xmult", 2); else if (c.enh === "lucky") { if (this.rand() < 1 / 5) apply(at, "mult", 20); if (this.rand() < 1 / 15) apply(at, "money", 20); }
        if (c.ed === "foil") apply(at, "chips", 50); else if (c.ed === "holo") apply(at, "mult", 10); else if (c.ed === "poly") apply(at, "xmult", 1.5);
        for (const [i, key] of active) for (const [kind, v] of this.onCard(key, c, firstFace)) apply(kind === "info" ? at : ["joker", i], kind, v);
      }
    });
    const mimes = active.filter(([, key]) => key === "Mime").length, held = r.hand.filter((c) => c.enh !== "stone"), lowest = held.length ? held.reduce((a, c) => (c.r < a.r ? c : a)).id : null;
    r.hand.forEach((c, h) => {                                            // cards held in hand
      if (this.debuffed(c)) return;
      for (let rep = 0; rep <= mimes; rep++) {
        const at = ["held", h];
        if (c.enh === "steel") apply(at, "xmult", 1.5);
        if (c.enh === "stone") continue;
        for (const [, key] of active) { if (key === "Baron" && c.r === 13) apply(at, "xmult", 1.5); else if (key === "Shoot the Moon" && c.r === 12) apply(at, "mult", 13); else if (key === "Raised Fist" && c.id === lowest) apply(at, "mult", 2 * CA.rankChips(c.r)); }
      }
    });
    for (const [i, key, src] of active) {                                 // the Jokers themselves, left to right
      const j = this.jokers[i];
      if (j.ed === "foil") apply(["joker", i], "chips", 50); else if (j.ed === "holo") apply(["joker", i], "mult", 10);
      for (const [kind, v] of this.independent(key, src, name, contains, cards)) apply(["joker", i], kind, v);
      if (j.ed === "poly") apply(["joker", i], "xmult", 1.5);
    }
    const total = Math.floor(t.chips * t.mult);
    for (const c of live) if (c.enh === "glass" && this.rand() < 0.25) { r.broken.push(c.id); apply(["played", pos[c.id]], "info", "Broken!"); }   // (afterwards: glass breaks, ice cream melts)
    this.jokers.forEach((j, i) => { if (j.k === "Ice Cream") { j.st.v -= 5; if (j.st.v <= 0) { j.dead = true; apply(["joker", i], "info", "Melted!"); } } });
    return total;
  }
  // the played cards to the discard pile; then the round won, lost, or drawn back up
  afterPlay() {
    const r = this.rnd, broken = new Set(r.broken);
    r.discard.push(...r.played.filter((c) => !broken.has(c.id))); if (broken.size) this.deck = this.deck.filter((c) => !broken.has(c.id));
    r.broken = []; r.played = []; this.jokers = this.jokers.filter((j) => !j.dead);
    if (r.score >= r.target) { this.winRound(); return; }
    if (r.hands <= 0) { this.stage = "over"; return; }
    if (r.boss === "The Hook") for (let k = 0; k < Math.min(2, r.hand.length); k++) { const c = this.choice(r.hand); r.hand.splice(r.hand.indexOf(c), 1); r.discard.push(c); }
    this.drawUp(r.boss === "The Serpent" ? 3 : undefined); this.crimson();
    if (!r.hand.length) this.stage = "over";
  }
  discard(idx) {
    const r = this.rnd; idx = [...new Set(idx)].sort((a, b) => a - b);
    if (!r || r.discards <= 0 || idx.length < 1 || idx.length > 5 || r.played.length) return false;
    const cards = idx.map((i) => r.hand[i]), ids = new Set(cards.map((c) => c.id));
    r.hand = r.hand.filter((c) => !ids.has(c.id)); r.discard.push(...cards); r.discards -= 1; r.discardsUsed += 1;
    for (const j of this.jokers) if (j.k === "Green Joker") j.st.v = Math.max(0, j.st.v - 1);
    this.drawUp(r.boss === "The Serpent" ? 3 : undefined);
    if (!r.hand.length) this.stage = "over";
    return true;
  }
  winRound() {
    const r = this.rnd, green = this.deckName === "Green Deck", lines = [[r.name, r.reward]];
    if (r.hands) lines.push([`${r.hands} hands left ($${green ? 2 : 1} each)`, r.hands * (green ? 2 : 1)]);
    if (green && r.discards) lines.push([`${r.discards} discards left ($1 each)`, r.discards]);
    for (const j of this.jokers) { const k = j.k; if (k === "Golden Joker") lines.push(["Golden Joker", 4]); else if (k === "Cloud 9" && this.nines()) lines.push(["Cloud 9", this.nines()]); else if (k === "Rocket") lines.push(["Rocket", j.st.v]); else if (k === "Delayed Gratification" && r.discardsUsed === 0 && r.discards) lines.push(["Delayed Gratification", 2 * r.discards]); }
    const gold = r.hand.filter((c) => c.enh === "gold" && !this.debuffed(c)).length * 3; if (gold) lines.push(["Gold Cards held in hand", gold]);
    if (!green) { const cap = this.vouchers.includes("Seed Money") ? 10 : 5, interest = Math.min(Math.floor(Math.max(0, this.money) / 5), cap); if (interest) { lines.push([`Interest ($1 for every $5, max $${cap})`, interest]); for (let k = 0; k < this.count("To the Moon"); k++) lines.push(["To the Moon", interest]); } }
    const boss = r.kind === "boss";
    if (boss) while (this.pendingTags.includes("Investment Tag")) { this.pendingTags.splice(this.pendingTags.indexOf("Investment Tag"), 1); lines.push(["Investment Tag", 25]); }
    const notes = [];
    for (const j of this.jokers) {
      const k = j.k;
      if (k === "Egg") j.sell += 3;
      else if (k === "Popcorn") { j.st.v -= 4; if (j.st.v <= 0) { j.dead = true; notes.push("The Popcorn's all eaten."); } }
      else if (k === "Gros Michel" && this.rand() < 1 / 6) { j.dead = true; this.extinct = true; notes.push("Gros Michel went extinct!"); }
      else if (k === "Cavendish" && this.rand() < 1 / 1000) { j.dead = true; notes.push("Cavendish went extinct!"); }
      else if (k === "Rocket" && boss) j.st.v += 2;
    }
    this.jokers = this.jokers.filter((j) => !j.dead);
    this.discardsUnused += r.discards; this.cash = lines; this.notes = notes; this.blindState[this.blind] = "beaten"; this.lastWasBoss = boss; this.lastBlind = { kind: r.kind, ante: this.ante, index: this.blind }; this.roundNo += 1; this.rnd = null; this.stage = "cashout";
    if (boss && this.ante >= 8 && !this.endless) this.won = true;
  }
  cashTotal() { return this.cash.reduce((s, [, v]) => s + v, 0); }
  collect() { this.money += this.cashTotal(); this.cash = []; this.notes = []; if (this.lastWasBoss) { this.ante += 1; this.blind = 0; this.newAnte(); } else this.blind += 1; this.makeShop(); this.stage = "shop"; }
  // ---- the shop ----
  floorMoney() { return this.has("Credit Card") ? -20 : 0; }
  price(base) { return this.vouchers.includes("Clearance Sale") ? Math.max(1, Math.floor(base * 0.75)) : base; }
  shopCard(exclude) {
    const tw = this.vouchers.includes("Tarot Merchant") ? 8 : 4, pw = this.vouchers.includes("Planet Merchant") ? 8 : 4, x = this.rand() * (20 + tw + pw);
    if (x < 20) { const key = this.randomJokerKey(null, exclude); exclude.add(key); const j = this.newJoker(key, this.rollEdition()), base = CA.JOKERS[key][2] + (CA.EDITION_COST[j.ed] || 0); return { type: "joker", item: j, base, price: this.price(base) }; }
    if (x < 20 + tw) return { type: "tarot", item: this.choice(Object.keys(CA.TAROTS)), base: 3, price: this.price(3) };
    return { type: "planet", item: this.choice(this.planetPool()), base: 3, price: this.price(3) };
  }
  packItem() { let x = this.rand() * CA.PACK_WEIGHTS.reduce((s, w) => s + w[2], 0), kind, size; for (const w of CA.PACK_WEIGHTS) { kind = w[0]; size = w[1]; x -= w[2]; if (x <= 0) break; } const base = CA.PACK_SIZES[size][1]; return { type: "pack", kind, size, base, price: this.price(base) }; }
  makeShop() {
    const ex = new Set(), cards = []; for (let i = 0; i < this.shopSlots; i++) cards.push(this.shopCard(ex));
    const packs = [this.packItem(), this.packItem()]; let reroll = 5 - (this.vouchers.includes("Reroll Surplus") ? 2 : 0);
    for (const tag of this.pendingTags.slice()) {
      if (tag === "Uncommon Tag" || tag === "Rare Tag") { const j = this.newJoker(this.randomJokerKey(tag === "Uncommon Tag" ? 2 : 3), this.rollEdition()); cards[0] = { type: "joker", item: j, base: 0, price: 0 }; }
      else if (tag === "Coupon Tag") for (const it of cards.concat(packs)) { it.base = 0; it.price = 0; }
      else if (tag === "D6 Tag") reroll = 0;
      else continue;
      this.pendingTags.splice(this.pendingTags.indexOf(tag), 1);
    }
    const voucher = this.voucherOffer ? { type: "voucher", item: this.voucherOffer, base: 10, price: this.price(10) } : null;
    this.shop = { cards, packs, voucher, reroll, free: this.count("Chaos the Clown") };
  }
  reroll() {
    const s = this.shop;
    if (s.free > 0) s.free -= 1; else if (this.money - s.reroll < this.floorMoney()) return "Not enough money"; else { this.money -= s.reroll; s.reroll += 1; }
    const ex = new Set(); s.cards = []; for (let i = 0; i < this.shopSlots; i++) s.cards.push(this.shopCard(ex));
    return null;
  }
  buy(where, i = 0) {
    const s = this.shop, item = where === "voucher" ? s.voucher : s[where][i];
    if (!item) return "Sold out";
    const price = item.price; if (price > 0 && this.money - price < this.floorMoney()) return "Not enough money";
    const t = item.type;
    if (t === "joker" && this.jokers.length >= this.jokerSlots) return "No room for another Joker";
    if ((t === "tarot" || t === "planet") && this.consumables.length >= this.consSlots) return "No room for another consumable";
    this.money -= price;
    if (where === "voucher") { s.voucher = null; this.voucherOffer = null; } else s[where][i] = null;
    if (t === "joker") { item.item.sell = Math.max(1, Math.floor(price / 2)); this.jokers.push(item.item); }
    else if (t === "tarot" || t === "planet") this.consumables.push({ k: item.item, type: t });
    else if (t === "pack") this.openPack(item.kind, item.size, "shop");
    else if (t === "voucher") this.applyVoucher(item.item);
    return null;
  }
  applyVoucher(v) {
    this.vouchers.push(v); const s = this.shop;
    if (v === "Overstock") { this.shopSlots += 1; if (s) s.cards.push(this.shopCard(new Set(s.cards.filter((c) => c && c.type === "joker").map((c) => c.item.k)))); }
    else if (v === "Crystal Ball") this.consSlots += 1; else if (v === "Antimatter") this.jokerSlots += 1;
    else if (v === "Reroll Surplus" && s) s.reroll = Math.max(0, s.reroll - 2);
    else if (v === "Clearance Sale" && s) for (const it of s.cards.concat(s.packs)) if (it && it.price) it.price = this.price(it.base);
  }
  nextRound() { this.shop = null; this.stage = "blind"; }
  sellJoker(i) { const j = this.jokers.splice(i, 1)[0]; this.money += j.sell; if (this.rnd && this.rnd.boss === "Verdant Leaf") this.rnd.leaf = false; if (this.rnd && this.rnd.disabled === j.id) this.rnd.disabled = null; return j; }
  sellConsumable(i) { this.consumables.splice(i, 1); this.money += 1; }
  // ---- packs ----
  openPack(kind, size, back) {
    let [, , n, picks] = CA.PACK_SIZES[size]; if (kind === "Buffoon") n = size === "normal" ? 2 : 4;
    let choices;
    if (kind === "Arcana") choices = this.sample(Object.keys(CA.TAROTS), n).map((t) => ({ type: "tarot", item: t }));
    else if (kind === "Celestial") { const pool = this.planetPool(); choices = (pool.length >= n ? this.sample(pool, n) : Array.from({ length: n }, () => this.choice(pool))).map((p) => ({ type: "planet", item: p })); }
    else if (kind === "Buffoon") { const ex = new Set(); choices = []; for (let k = 0; k < n; k++) { const key = this.randomJokerKey(null, ex); ex.add(key); choices.push({ type: "joker", item: this.newJoker(key, this.rollEdition()) }); } }
    else choices = Array.from({ length: n }, () => ({ type: "card", item: this.randomCard() }));
    let hand = [];
    if (kind === "Arcana") { const pile = this.shuffle(this.deck.slice()), sz = this.handSizeBase + (this.vouchers.includes("Paint Brush") ? 1 : 0) + this.count("Juggler"); hand = pile.slice(0, sz).map((c) => c.id); }   // (a hand to use the tarots on)
    this.pack = { kind, size, choices, picks, back, hand }; this.stage = "pack";
  }
  packHand() { if (!this.pack) return []; const byId = {}; for (const c of this.deck) byId[c.id] = c; return this.pack.hand.map((i) => byId[i]).filter(Boolean); }
  packPick(i, sel = []) {
    const pk = this.pack, ch = pk.choices[i]; let msg = null;
    if (ch.type === "tarot") { const [ok, m] = this.useTarot(ch.item, sel); if (!ok) return [false, m]; msg = m; }
    else if (ch.type === "planet") msg = this.usePlanet(ch.item);
    else if (ch.type === "joker") { if (this.jokers.length >= this.jokerSlots) return [false, "No room for another Joker"]; this.jokers.push(ch.item); }
    else { this.deck.push(ch.item); msg = "Added to your deck"; }
    pk.choices.splice(i, 1); pk.picks -= 1;
    if (pk.picks <= 0 || !pk.choices.length) this.closePack();
    return [true, msg];
  }
  closePack() { const back = this.pack ? this.pack.back : "shop"; this.pack = null; this.stage = back; }
  // ---- Tarots and Planets ----
  usePlanet(name) { const hand = CA.PLANETS[name]; this.levels[hand] += 1; for (const j of this.jokers) if (j.k === "Constellation") j.st.v += 1; this.lastUsed = name; return `${hand}: level ${this.levels[hand]}`; }
  destroy(cards) { const ids = new Set(cards.map((c) => c.id)); this.deck = this.deck.filter((c) => !ids.has(c.id)); if (this.rnd) this.rnd.hand = this.rnd.hand.filter((c) => !ids.has(c.id)); }
  useTarot(name, sel) {
    const [, lo, hi] = CA.TAROTS[name];
    if (lo && !(sel.length >= lo && sel.length <= hi)) return [false, lo === hi ? `Select ${lo} card${lo > 1 ? "s" : ""}` : `Select ${lo} to ${hi} cards`];
    const room = this.consSlots - this.consumables.length; let msg = null;
    if (CA.ENH_TAROT[name]) for (const c of sel) c.enh = CA.ENH_TAROT[name];
    else if (CA.SUIT_TAROT[name]) for (const c of sel) c.s = CA.SUIT_TAROT[name];
    else if (name === "Strength") for (const c of sel) c.r = c.r === 14 ? 2 : c.r + 1;
    else if (name === "The Hanged Man") this.destroy(sel);
    else if (name === "Death") { const [left, right] = sel; for (const k of Object.keys(right)) if (k !== "id") left[k] = right[k]; }
    else if (name === "The Fool") { if (!this.lastUsed) return [false, "Nothing to copy yet"]; if (room <= 0) return [false, "No room for a consumable"]; this.consumables.push({ k: this.lastUsed, type: CA.PLANETS[this.lastUsed] ? "planet" : "tarot" }); }
    else if (name === "The High Priestess") { if (room <= 0) return [false, "No room for a consumable"]; for (let k = 0; k < Math.min(2, room); k++) this.consumables.push({ k: this.choice(this.planetPool()), type: "planet" }); }
    else if (name === "The Emperor") { if (room <= 0) return [false, "No room for a consumable"]; for (let k = 0; k < Math.min(2, room); k++) this.consumables.push({ k: this.choice(Object.keys(CA.TAROTS).filter((t) => t !== "The Fool")), type: "tarot" }); }
    else if (name === "The Hermit") { const gain = Math.min(Math.max(0, this.money), 20); this.money += gain; msg = `+$${gain}`; }
    else if (name === "Temperance") { const gain = Math.min(50, this.jokers.reduce((s, j) => s + j.sell, 0)); this.money += gain; msg = `+$${gain}`; }
    else if (name === "The Wheel of Fortune") { const plain = this.jokers.filter((j) => !j.ed); if (!plain.length) return [false, "No Joker to improve"]; if (this.rand() < 0.25) { const j = this.choice(plain), x = this.rand(); j.ed = x < 0.5 ? "foil" : x < 0.85 ? "holo" : "poly"; msg = `${j.k} is now ${CA.EDITIONS[j.ed][0]}!`; } else msg = "Nope!"; }
    else if (name === "Judgement") { if (this.jokers.length >= this.jokerSlots) return [false, "No room for a Joker"]; this.jokers.push(this.newJoker(this.randomJokerKey(), this.rollEdition())); }
    if (name !== "The Fool") this.lastUsed = name;
    return [true, msg];
  }
  useConsumable(i, sel = []) { const c = this.consumables.splice(i, 1)[0]; if (c.type === "planet") return [true, this.usePlanet(c.k)]; const [ok, msg] = this.useTarot(c.k, sel); if (!ok) this.consumables.splice(i, 0, c); return [ok, msg]; }
  mostPlayed() { const h = Object.keys(this.played).reduce((a, k) => (this.played[k] > this.played[a] ? k : a)); return this.played[h] ? h : null; }
};

// ---- the house: wagers, payouts and the unlocks, kept with the village ----
// A wager is paid at the table. Each blind beaten pays back a share of it - the small 40%, the big 60%, the boss
// 100% - growing by a quarter for each ante past the first; beating the eighth ante's boss pays five wagers more.
// A wager of nothing pays nothing, and still unlocks: a Joker for every blind ever beaten (25 to start, in the
// order below), and the decks by milestones.
CM.CASINO = { name: "The Gilded Joker", wagers: [0, 10, 25, 50, 100, 250, 500], share: [0.4, 0.6, 1.0], antePer: 0.25, winBonus: 5, startJokers: 25 };
CM.CA_JOKER_ORDER = Object.keys(CA.JOKERS).sort((a, b) => CA.JOKERS[a][1] - CA.JOKERS[b][1]);   // (commons first, then uncommons, then rares; in the book's order)
CM.CA_DECK_UNLOCKS = {
  "Red Deck": { why: "", ok: () => true },
  "Blue Deck": { why: "Beat a Boss Blind", ok: (K) => K.bosses >= 1 },
  "Yellow Deck": { why: "Reach Ante 3", ok: (K) => K.maxAnte >= 3 },
  "Green Deck": { why: "Reach Ante 4", ok: (K) => K.maxAnte >= 4 },
  "Black Deck": { why: "Beat 6 Boss Blinds, all told", ok: (K) => K.bosses >= 6 },
  "Abandoned Deck": { why: "Play a Straight Flush", ok: (K) => (K.hands["Straight Flush"] || 0) > 0 },
  "Checkered Deck": { why: "Reach Ante 6", ok: (K) => K.maxAnte >= 6 },
  "Erratic Deck": { why: "Win a run (beat Ante 8)", ok: (K) => K.wins >= 1 },
};
CM.casinoPayout = (wager, ante, index) => Math.floor(wager * CM.CASINO.share[index] * (1 + CM.CASINO.antePer * (ante - 1)));
Object.assign(CM.Game.prototype, {
  casino() {
    this.village = this.village || {};
    const K = this.village.casino = this.village.casino || {};
    for (const k of ["blinds", "bosses", "maxAnte", "wins", "runs", "bestHand", "wagered", "paid"]) K[k] = K[k] || 0;
    K.hands = K.hands || {}; K.run = K.run || null; K.wager = K.wager || 0; K.deck = K.deck || "Red Deck";
    return K;
  },
  casinoJokers() { const K = this.casino(); return CM.CA_JOKER_ORDER.slice(0, Math.min(CM.CA_JOKER_ORDER.length, CM.CASINO.startJokers + K.blinds)); },
  casinoDecks() { const K = this.casino(); return Object.keys(CA.DECKS).filter((d) => CM.CA_DECK_UNLOCKS[d].ok(K)); },
  saveCasino() { if (this.saveVillage) this.saveVillage(); },
  // a run dealt: the wager paid (if any), the deck if it is unlocked
  casinoDeal(deck, wager) {
    const K = this.casino();
    if (K.run) return "There is a game on the table already.";
    if (!this.casinoDecks().includes(deck)) return `The ${deck} is not unlocked: ${CM.CA_DECK_UNLOCKS[deck].why}.`;
    wager = Math.max(0, Math.floor(wager || 0));
    if (wager > this.gold) return `A wager of ${wager} gold, and the party has ${this.gold}.`;
    this.gold -= wager; K.wagered += wager; K.runs += 1; K.wager = wager; K.deck = deck;
    const run = new CM.CaRun(deck, CM.hashSeed(`${this.seed}:claudeatro:${K.runs}`), this.casinoJokers());
    run.wager = wager; run.paid = 0; K.run = run.toJSON();
    this.saveCasino(); this.saveRun && this.saveRun();
    return "";
  },
  casinoRun() { const K = this.casino(); if (!K.run) return null; if (!this.caRunLive || this.caRunLive.__src !== K.run) { this.caRunLive = CM.CaRun.fromJSON(K.run); this.caRunLive.__src = K.run; } return this.caRunLive; },
  casinoKeep(run) { const K = this.casino(); const d = run.toJSON(); delete d.__src; K.run = d; run.__src = d; this.caRunLive = run; this.saveCasino(); },
  // after a hand: the round's milestones; after a round: the house pays, and the unlocks; returns what is new
  casinoAfterHand(run, res) {
    const K = this.casino(); if (res && res.hand) K.hands[res.hand] = (K.hands[res.hand] || 0) + 1; K.bestHand = Math.max(K.bestHand, res ? res.total : 0);
    const out = { paid: 0, jokers: [], decks: [] };
    if (run.stage === "cashout" && run.lastBlind && !run.paidFor) {
      const B = run.lastBlind, decksBefore = this.casinoDecks(), jokersBefore = this.casinoJokers();
      K.blinds += 1; if (B.kind === "boss") K.bosses += 1; K.maxAnte = Math.max(K.maxAnte, B.kind === "boss" ? B.ante + 1 : B.ante);
      let pay = CM.casinoPayout(run.wager || 0, B.ante, B.index); if (B.kind === "boss" && B.ante === 8 && !run.endless) { pay += (run.wager || 0) * CM.CASINO.winBonus; K.wins += 1; }
      if (pay) { this.gold += pay; run.paid = (run.paid || 0) + pay; K.paid += pay; }
      out.paid = pay; run.paidFor = `${B.ante}:${B.index}`;
      out.jokers = this.casinoJokers().filter((k) => !jokersBefore.includes(k)); out.decks = this.casinoDecks().filter((d) => !decksBefore.includes(d));
      run.pool = this.casinoJokers();
    }
    if (run.stage === "blind" || run.stage === "shop") run.paidFor = null;
    if (run.stage === "over") { out.over = { ante: run.ante, wager: run.wager || 0, paid: run.paid || 0 }; K.maxAnte = Math.max(K.maxAnte, run.ante); K.run = null; this.caRunLive = null; this.saveCasino(); this.saveRun && this.saveRun(); return out; }
    this.casinoKeep(run); this.saveRun && this.saveRun();
    return out;
  },
  casinoQuit() { const K = this.casino(); K.run = null; this.caRunLive = null; this.saveCasino(); },
});
