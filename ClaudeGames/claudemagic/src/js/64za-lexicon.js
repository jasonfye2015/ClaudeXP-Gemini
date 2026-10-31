"use strict";
// The Lexicon Engine (the twenty-sixth big update - v13.6): an artificer's terminal in a corner of the Gilded Joker, a
// green glass screen in a brass case. Its memory is shown as rows of symbols, and words are hidden among them: one is
// the engine's password. Choose a word and the engine tells you its likeness - how many of its letters stand in the same
// places as the password's; four tries, and the engine locks. A pair of brackets with only symbols between them on one
// row - () [] {} <> - can be chosen too: it takes out a dud word, or (now and then) gives the tries back. Ten levels,
// the words longer and more of them as they go; each level cracked pays gold and a Claudescryption card the first time
// (common to four, a stronger one to nine, a rare at ten). It costs nothing to sit down. The window is 76q-lexicon.js.
CM.LX = {
  tries: 4, cols: 2, rows: 16, width: 12, JUNK: "!@#$%^&*-_=+;:'\",./?\\|`~",
  LEVELS: [[5, 8, 4], [5, 10, 4], [6, 11, 4], [6, 13, 4], [7, 14, 4], [7, 16, 4], [8, 16, 3], [8, 18, 3], [9, 18, 3], [10, 20, 3]],   // (word length, words, tries)
  gold: (n) => 15 + n * 12,
  WORDS: {
    5: "BLADE BLOOD BONES CHARM CLOAK CRYPT CURSE DWARF EMBER FAIRY FLAME GHOST GIANT GLOOM GRAVE GUARD HAVEN HEART KNAVE LANCE MAGIC MAPLE QUEST RAVEN RELIC RUNES SABLE SHADE SKULL SLIME SPEAR SPELL STAFF STONE SWORD THORN TOMES TORCH TOWER TROLL VAULT VENOM WITCH WRAIT".split(" ").filter((w) => w.length === 5),
    6: "ARCANE BANNER BEACON CANDLE CASTLE CHALKS CINDER COFFIN DAGGER DRAGON FOREST GOBLIN GOLDEN HAMMER HOLLOW KNIGHT LAVISH LEGEND MANTLE MARROW MINION ORACLE POTION RAVENS RITUAL SCROLL SHIELD SILVER SPIRIT SPRITE SUMMON TALONS TEMPLE THRONE TIMBER VELVET WARDEN WIZARD WRAITH ZEALOT".split(" "),
    7: "ALCHEMY AMULETS ANCIENT BANSHEE BASTION CAULDRON CHALICE CRIMSON DUNGEON ELIXIRS EMBLEMS FORTUNE GARGOYL GAUNTLE HALBERD HARBOUR JOURNEY KINGDOM LANTERN MYSTICS NIGHTLY ORCHARD PHANTOM PILGRIM QUARREL RAMPART SCEPTER SHADOWS SORCERY SPECTER TALISMAN TAVERNS THUNDER TRINKET VAMPIRE VILLAGE WARLOCK WARRIOR WYVERNS".split(" ").filter((w) => w.length === 7),
    8: "ALCHEMIC AMETHYST BARONESS BASILISK CATACOMB CHAMPION CITADELS CROSSBOW DESOLATE DOMINION ENCHANTS FLAGSTONE FORTRESS GAUNTLET GRIMOIRE HEIRLOOM INCANTED LABYRINTH LOCKSMITH MANTICORE MIDNIGHT MONASTERY NECROTIC OBSIDIAN PALADINS PARCHMENT PORTCULIS RELIQUARY SANCTUMS SCABBARD SEPULCHER SORCERER SPELLING STRONGHOLD TAPESTRY TREASURY VANGUARD WATCHMEN WILDFIRE".split(" ").filter((w) => w.length === 8),
    9: "ALCHEMIST APPARITION BATTLEAXE BLACKSMITH CANDLELIT CATACOMBS CHAMPIONS CLOCKWORK CROSSBOWS DEATHLESS DUNGEONS ENCHANTED FIREBRAND FORGOTTEN GATEHOUSE GRAVEYARD HEIRLOOMS LABYRINTH LANTERNED LOCKSMITH MAGICIANS MANTICORE MOONSTONE NECROMANT NIGHTSHADE OBSIDIANS PARCHMENT PORTCULLIS REVENANTS SANCTUARY SEPULCHRE SPELLBOOK STARLIGHT STONEWALL SWORDSMAN TREASURES UNDERHALL WANDERERS WATCHTOWER WITCHLIGHT".split(" ").filter((w) => w.length === 9),
    10: "ADVENTURER APPARITION BATTLEMENT BLACKSMITH CANDLEWICK CHANCELLOR CHRONICLES CLOCKWORKS CONJURATION DEATHKNELL DOPPELGANG ENCHANTING EVERBURNING FIREBRANDS GATEKEEPER GRAVESTONE HEADSTONES HUNTRESSES INCANTATION KNIGHTHOOD LIGHTHOUSE MOONSTONES NECROMANCY NIGHTSHADE PORTCULLIS RUNESMITHS SANCTUARIES SHAPESHIFT SPELLBOUND STARLIGHTS STONEMASON SWORDSMITH THUNDERCAP TREASURIES UNDERCROFT WATCHTOWER WILDERNESS WITCHCRAFT WORMWOODEN".split(" ").filter((w) => w.length === 10),
  },
};
const LX = CM.LX;
LX.likeness = (a, b) => { let n = 0; for (let i = 0; i < a.length; i++) if (a[i] === b[i]) n++; return n; };
// a tier's card, the Runestack way: common, a stronger common, rare
CM.Game.prototype.cgTierCard = function (kind, why, R) {
  if (kind === "better") { const pool = CM.CARD_BETTER; const card = pool[R.int(0, pool.length - 1)]; this.addCard(card, why); this.cgStore().cards.push(card); this.tally.casinoCards = (this.tally.casinoCards || 0) + 1; return card; }
  return this.cgCard(kind === "rare", why, R);
};
CM.cardTierFor = (n) => (n >= 10 ? "rare" : n >= 5 ? "better" : "common");
LX.Puzzle = class {
  constructor(level, seed) {
    const [len, count, tries] = LX.LEVELS[level - 1], R = this.rnd = new CM.Random(seed), pool = LX.WORDS[len].slice(); this.level = level; this.len = len; this.tries = this.maxTries = tries; this.stage = "play"; this.log = []; this.used = new Set(); this.removed = new Set();
    this.answer = pool.splice(R.int(0, pool.length - 1), 1)[0];
    pool.sort((a, b) => LX.likeness(b, this.answer) - LX.likeness(a, this.answer) || R.next() - 0.5);        // (some near the password, some far)
    const near = pool.slice(0, Math.ceil(count * 0.6)), far = pool.slice(Math.ceil(count * 0.6)); const words = [this.answer];
    while (words.length < count && (near.length || far.length)) { const from = near.length && (R.chance(0.6) || !far.length) ? near : far; words.push(from.splice(R.int(0, from.length - 1), 1)[0]); }
    // the memory: rows of symbols with the words laid in (never two touching), and bracket pairs here and there
    const W = LX.width, total = LX.cols * LX.rows * W, J = LX.JUNK, chars = []; for (let i = 0; i < total; i++) chars.push(J[R.int(0, J.length - 1)]);
    this.words = []; const order = words.slice(); for (let i = order.length - 1; i > 0; i--) { const j = R.int(0, i); [order[i], order[j]] = [order[j], order[i]]; }
    const slot = Math.floor(total / order.length);
    order.forEach((w, k) => { let at = 0; for (let tries = 0; tries < 50; tries++) { at = k * slot + R.int(1, Math.max(1, slot - w.length - 1)); if (at + w.length < total) break; } for (let i = 0; i < w.length; i++) chars[at + i] = w[i]; this.words.push({ w, at }); });
    this.chars = chars; this.brackets = []; const isLetter = (c) => c >= "A" && c <= "Z";
    for (let row = 0; row < LX.cols * LX.rows; row++) { if (!R.chance(0.35)) continue; const [o, c] = R.pick([["(", ")"], ["[", "]"], ["{", "}"], ["<", ">"]]), s0 = row * W, a = s0 + R.int(0, W - 3), b = Math.min(s0 + W - 1, a + R.int(1, 5)); let clean = true; for (let i = a; i <= b; i++) if (isLetter(chars[i])) clean = false; if (!clean) continue; chars[a] = o; chars[b] = c; for (let i = a + 1; i < b; i++) if ("()[]{}<>".includes(chars[i])) chars[i] = "."; this.brackets.push({ a, b }); }
  }
  wordAt(i) { return this.words.find((x) => i >= x.at && i < x.at + x.w.length) || null; }
  bracketAt(i) { return this.brackets.find((x) => x.a === i && !this.used.has(x.a)) || null; }
  // a word chosen: its likeness, or the way in
  choose(w) {
    if (this.stage !== "play" || this.removed.has(w)) return null;
    if (w === this.answer) { this.stage = "won"; this.log.push(`>${w}`, ">Exact match!", ">Please wait", ">while system", ">is accessed."); return { won: true }; }
    const like = LX.likeness(w, this.answer); this.tries -= 1; this.log.push(`>${w}`, ">Entry denied.", `>Likeness=${like}`); this.removed.add(w);
    if (this.tries <= 0) { this.stage = "locked"; this.log.push(">LOCKED."); } return { like };
  }
  // a bracket pair: a dud word taken out, or the tries back (one time in five, while tries are short)
  bracket(b) {
    if (this.stage !== "play" || this.used.has(b.a)) return null; this.used.add(b.a); const seq = this.chars.slice(b.a, b.b + 1).join("");
    const duds = this.words.filter((x) => x.w !== this.answer && !this.removed.has(x.w));
    if ((this.tries < this.maxTries && this.rnd.chance(0.2)) || !duds.length) { this.tries = this.maxTries; this.log.push(`>${seq}`, ">Allowance", ">replenished."); return { reset: true }; }
    const d = duds[this.rnd.int(0, duds.length - 1)]; this.removed.add(d.w); for (let i = d.at; i < d.at + d.w.length; i++) this.chars[i] = "."; this.log.push(`>${seq}`, ">Dud removed."); return { dud: d.w };
  }
};
Object.assign(CM.Game.prototype, {
  lxStore() { const F = this.cgStore(); F.lx = F.lx || { best: 0, n: 0, tries: 0 }; return F.lx; },
  lxStart(level) { const S = this.lxStore(); if (level < 1 || level > Math.min(LX.LEVELS.length, S.best + 1)) return { error: "That level is still locked." }; S.n += 1; S.tries += 1; this.lxLive = new LX.Puzzle(level, CM.hashSeed(`${this.seed}:lexicon:${level}:${S.n}`)); this.saveCasino && this.saveCasino(); return this.lxLive; },
  // cracked: gold and a card the first time a level is cracked
  lxCracked() {
    const P = this.lxLive, S = this.lxStore(); if (!P || P.stage !== "won" || P.paid) return null; P.paid = true; const n = P.level;
    if (n <= S.best) return { level: n, again: true };
    S.best = n; const gold = LX.gold(n); this.gold += gold; const F = this.cgStore(); F.paid.lexicon = (F.paid.lexicon || 0) + gold;
    const card = this.cgTierCard(CM.cardTierFor(n), `The Lexicon Engine, level ${n} cracked!`, new CM.Random(CM.hashSeed(`${this.seed}:lexicon:card:${n}`)));
    this.saveCasino && this.saveCasino(); this.emit("change"); return { level: n, gold, card, kind: CM.cardTierFor(n) };
  },
});
