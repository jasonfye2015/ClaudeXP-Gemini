"use strict";
// Claudescryption at the cabin in the Wood (the thirteenth update): Leshy's card game, the rules ported whole from the
// Timeline's own Claudescryption (ClaudeGames/claudescryption/game.py) so a game at the cabin plays as a game there.
// A battle is four lanes: your creatures in the bottom row, Leshy's above, the cards he means to play next behind
// them. You draw (your deck or a squirrel), play cards - blood paid by sacrificing your own creatures, bones from your
// dead - and ring the bell: your creatures strike lane by lane, then his. Tip the scale five teeth your way to win.
// The battle steps as a generator, so the table shows it one strike at a time. The collection and the deck are kept
// between runs, with the village (village.cards).

// name -> [emoji, blood, bones, power, health, sigils, rarity]   rarity: c common, r rare, t terrain, s special
CM.CARDS = {
  "Squirrel": ["🐿️", 0, 0, 0, 1, [], "s"], "Stoat": ["🦡", 1, 0, 1, 3, [], "c"], "Bullfrog": ["🐸", 1, 0, 1, 2, ["Mighty Leap"], "c"],
  "Wolf": ["🐺", 2, 0, 3, 2, [], "c"], "Wolf Cub": ["🐕", 1, 0, 1, 1, ["Fledgling"], "c"], "Raven": ["🐦‍⬛", 2, 0, 2, 3, ["Airborne"], "c"],
  "Sparrow": ["🐦", 1, 0, 1, 2, ["Airborne"], "c"], "Mantis": ["🦗", 1, 0, 1, 1, ["Bifurcated Strike"], "c"], "Mantis God": ["🙏", 1, 0, 0, 1, ["Trifurcated Strike"], "r"],
  "Adder": ["🐍", 2, 0, 1, 1, ["Touch of Death"], "c"], "Black Goat": ["🐐", 1, 0, 0, 1, ["Worthy Sacrifice"], "r"], "Cat": ["🐈", 1, 0, 0, 1, ["Many Lives"], "r"],
  "Grizzly": ["🐻", 3, 0, 4, 6, [], "c"], "Moose Buck": ["🫎", 3, 0, 3, 7, ["Sprinter"], "r"], "Elk": ["🦌", 2, 0, 2, 4, ["Sprinter"], "c"],
  "Elk Fawn": ["🦌", 1, 0, 1, 1, ["Sprinter", "Fledgling"], "c"], "Field Mice": ["🐁", 2, 0, 2, 2, ["Fecundity"], "c"], "Warren": ["🕳️", 1, 0, 0, 2, ["Rabbit Hole"], "c"],
  "Rabbit": ["🐇", 0, 0, 0, 1, [], "s"], "Beehive": ["🍯", 1, 0, 0, 2, ["Bees Within"], "c"], "Bee": ["🐝", 0, 0, 1, 1, ["Airborne"], "s"],
  "Porcupine": ["🦔", 1, 0, 1, 2, ["Sharp Quills"], "c"], "Skunk": ["🦨", 1, 0, 0, 3, ["Stinky"], "c"], "Mole": ["🐀", 1, 0, 0, 4, ["Burrower"], "c"],
  "Bloodhound": ["🐕‍🦺", 2, 0, 2, 3, ["Guardian"], "c"], "Kingfisher": ["🐟", 1, 0, 1, 1, ["Airborne", "Waterborne"], "c"], "River Snapper": ["🐢", 2, 0, 1, 6, [], "c"],
  "Coyote": ["🐾", 0, 4, 2, 1, [], "c"], "Opossum": ["🐭", 0, 2, 1, 1, [], "c"], "Vulture": ["🦅", 0, 8, 3, 3, ["Airborne"], "r"], "Rattler": ["🪱", 0, 6, 3, 1, [], "c"],
  "Alpha": ["🐺", 0, 4, 1, 2, ["Leader"], "c"], "Corpse Maggots": ["🐛", 0, 5, 1, 2, ["Corpse Eater"], "c"], "Beaver": ["🦫", 2, 0, 1, 3, ["Dam Builder"], "c"],
  "Ouroboros": ["🐉", 2, 0, 1, 1, ["Unkillable"], "r"], "Amalgam": ["🧬", 2, 0, 3, 3, [], "r"], "Pack Mule": ["🫏", 0, 0, 0, 5, ["Sprinter"], "s"],
  "Dam": ["🪵", 0, 0, 0, 2, [], "t"], "Boulder": ["🪨", 0, 0, 0, 5, [], "t"], "Grand Fir": ["🌲", 0, 0, 0, 3, ["Mighty Leap"], "t"], "Gold Nugget": ["🪙", 0, 0, 0, 2, [], "t"],
  "Steel Trap": ["🪤", 0, 0, 0, 1, ["Steel Trap"], "t"], "Bait Bucket": ["🪣", 0, 0, 0, 1, [], "t"], "The Moon": ["🌕", 0, 0, 1, 24, ["Mighty Leap", "All Lanes"], "s"],
};
CM.SIGILS = {
  "Airborne": ["🪶", "Attacks the opponent directly, flying over creatures."], "Mighty Leap": ["🦘", "Blocks Airborne attacks."], "Touch of Death": ["☠️", "Kills any creature it damages."],
  "Bifurcated Strike": ["✌️", "Strikes the lanes to its left and right."], "Trifurcated Strike": ["🔱", "Strikes the lanes to its left, ahead and right."],
  "Sprinter": ["💨", "Moves a lane at the end of its owner's turn."], "Fecundity": ["🥚", "When played, a copy goes into your hand."], "Unkillable": ["♾️", "When it dies, it returns to your hand."],
  "Worthy Sacrifice": ["🩸", "Counts as three blood when sacrificed."], "Many Lives": ["🐾", "Survives being sacrificed."], "Bone King": ["👑", "Gives four bones when it dies."],
  "Stinky": ["🤢", "The creature opposite it loses 1 power."], "Rabbit Hole": ["🕳️", "When played, a Rabbit goes into your hand."], "Bees Within": ["🐝", "When struck, a Bee goes into your hand."],
  "Sharp Quills": ["🌵", "Whatever strikes it takes 1 damage."], "Guardian": ["🛡️", "Moves to block a creature played opposite an empty lane."], "Burrower": ["⛏️", "Moves to block attacks on empty lanes."],
  "Leader": ["🚩", "Creatures beside it gain 1 power."], "Waterborne": ["🌊", "Submerged: attacks pass over it."], "Corpse Eater": ["🪱", "From your hand, takes the place of a creature of yours that dies."],
  "Dam Builder": ["🪵", "When played, builds Dams in the lanes beside it."], "Fledgling": ["🐣", "Grows up after a turn."], "Steel Trap": ["🪤", "When it dies, it kills the creature opposite."],
  "All Lanes": ["🌕", "Strikes every lane."],
};
CM.CARD_GROWS = { "Wolf Cub": "Wolf", "Elk Fawn": "Elk" };
CM.CARD_REGIONS = [
  { name: "The Woodlands", boss: "The Prospector", pool: ["Stoat", "Bullfrog", "Opossum", "Skunk", "Wolf Cub", "Sparrow", "Mantis", "Elk Fawn", "Coyote", "Alpha", "Raven", "Wolf"], terrain: ["Boulder", "Grand Fir"] },
  { name: "The Wetlands", boss: "The Angler", pool: ["Bullfrog", "Kingfisher", "Skunk", "Beehive", "Sparrow", "Beaver", "River Snapper", "Adder", "Corpse Maggots", "Field Mice", "Rattler", "Raven"], terrain: ["Boulder", "Bait Bucket"] },
  { name: "The Snow Line", boss: "The Trapper", pool: ["Stoat", "Opossum", "Porcupine", "Elk Fawn", "Mole", "Bloodhound", "Field Mice", "Raven", "Elk", "Adder", "Wolf", "Alpha", "Vulture", "Grizzly", "Moose Buck"], terrain: ["Grand Fir", "Boulder", "Steel Trap"] },
];
CM.CARD_BOSS_POOL = {
  "The Prospector": ["Stoat", "Pack Mule", "Coyote", "Bloodhound", "Wolf", "Alpha"], "The Angler": ["Bullfrog", "Bait Bucket", "Kingfisher", "Beehive", "River Snapper", "Adder"],
  "The Trapper": ["Porcupine", "Bloodhound", "Raven", "Elk", "Wolf", "Grizzly"], "Leshy": ["Porcupine", "Bloodhound", "Raven", "Adder", "Wolf", "Vulture", "Grizzly", "Moose Buck"],
};
CM.CARD_COMMONS = Object.keys(CM.CARDS).filter((n) => CM.CARDS[n][6] === "c");
CM.CARD_RARES = Object.keys(CM.CARDS).filter((n) => CM.CARDS[n][6] === "r");
CM.CARD_STARTER = ["Stoat", "Bullfrog", "Wolf", "Sparrow", "Mantis", "Opossum"];
CM.cardSpec = (name, kw = {}) => Object.assign({ name, power: 0, health: 0, sigils: [] }, kw);
CM.cardInfo = (s) => { const c = CM.CARDS[s.name], sig = c[5].concat((s.sigils || []).filter((g) => !c[5].includes(g))); return { emoji: c[0], blood: c[1], bones: c[2], power: c[3] + (s.power || 0), health: c[4] + (s.health || 0), sigils: sig }; };

CM.CardCreature = class {
  constructor(s, owner) { const I = CM.cardInfo(s); this.spec = s; this.owner = owner; this.emoji = I.emoji; this.blood = I.blood; this.bones = I.bones; this.basePower = I.power; this.maxHealth = I.health; this.health = I.health; this.sigils = I.sigils; this.name = s.name; this.turns = 0; this.direction = 1; }
  has(g) { return this.sigils.includes(g); }
};

CM.CardBattle = class {
  // region 0-2, difficulty 0-3, boss a name or null
  constructor(deck, region, difficulty, boss = null, seed = 1) {
    this.rng = new CM.Random(typeof seed === "number" ? seed : CM.hashSeed(String(seed)));
    this.region = region; this.difficulty = difficulty; this.boss = boss; this.phase = 1;
    this.you = [null, null, null, null]; this.leshy = [null, null, null, null]; this.queue = [null, null, null, null];
    this.deck = deck.map((s) => Object.assign({}, s)); this.rng.shuffle(this.deck);
    this.squirrels = 20; this.hand = []; this.bones = 0; this.scale = 0; this.turn = 0; this.drawn = true; this.over = null; this.log = []; this.tricks = 0; this.rising = false;
    this.hand.push(CM.cardSpec("Squirrel")); for (let i = 0; i < 3; i++) this.drawDeck();
    this.plan = this.makePlan(); this.leshyTurnPlays(0);
    if (!boss && this.rng.next() < 0.35) { const lane = this.rng.int(0, 3); this.leshy[lane] = new CM.CardCreature(CM.cardSpec(this.rng.pick(CM.CARD_REGIONS[region].terrain)), "leshy"); }
  }
  say(t) { this.log.push(t); this.log = this.log.slice(-6); }
  makePlan() {
    const reg = CM.CARD_REGIONS[this.region], pool = (CM.CARD_BOSS_POOL[this.boss] || reg.pool).slice(), plan = [], strength = 1 + this.difficulty;
    const reach = Math.min(pool.length, Math.floor(2 + strength * 2)), counts = ({ 1: [0, 1, 1], 2: [0, 1, 1, 1, 2], 3: [1, 1, 1, 2] })[Math.round(strength)] || [1, 1, 2, 2];
    for (let t = 0; t < 40; t++) {
      const k = t < 2 ? 1 : this.rng.pick(counts), turn = [];
      for (let i = 0; i < k; i++) { const ramp = this.boss ? 1 + Math.floor(t / 2) : 2 + t; turn.push(CM.cardSpec(this.rng.pick(pool.slice(0, Math.min(reach, ramp))))); }
      plan.push(turn);
    }
    return plan;
  }
  leshyTurnPlays(t) {
    for (const s of t < this.plan.length ? this.plan[t] : []) {
      const free = [0, 1, 2, 3].filter((i) => !this.queue[i]); if (!free.length) break;
      this.queue[this.rng.pick(free)] = new CM.CardCreature(s, "leshy");
    }
  }
  drawDeck() { if (this.deck.length) { this.hand.push(this.deck.pop()); return true; } return false; }
  draw(pile) {
    if (this.drawn || this.over) return false;
    if (pile === "deck" && this.deck.length) this.drawDeck();
    else if (pile === "squirrel" && this.squirrels > 0) { this.squirrels -= 1; this.hand.push(CM.cardSpec("Squirrel")); }
    else if (!this.deck.length && this.squirrels <= 0) { /* nothing left */ }
    else return false;
    this.drawn = true; return true;
  }
  canDraw() { return !this.drawn && (this.deck.length > 0 || this.squirrels > 0); }
  bloodOf(lanes) { return lanes.reduce((s, i) => s + (this.you[i] ? (this.you[i].has("Worthy Sacrifice") ? 3 : 1) : 0), 0); }
  canAfford(card) { const I = CM.cardInfo(card); if (I.bones && this.bones < I.bones) return false; if (I.blood) return this.bloodOf([0, 1, 2, 3].filter((i) => this.you[i])) >= I.blood; return true; }
  play(handIndex, lane, sacrifices = []) {
    const card = this.hand[handIndex]; if (!card || this.over) return false;
    const I = CM.cardInfo(card);
    if (I.bones > this.bones || this.bloodOf(sacrifices) < I.blood) return false;
    if (this.you[lane] && !sacrifices.includes(lane)) return false;
    for (const i of sacrifices) { const c = this.you[i]; if (!c || c.has("Many Lives")) continue; this.you[i] = null; this.died(c, i, "you", true); }
    if (this.you[lane]) return false;
    this.bones -= I.bones; this.hand.splice(handIndex, 1);
    const c = new CM.CardCreature(card, "you"); this.you[lane] = c; this.onPlay(c, lane, "you");
    return true;
  }
  onPlay(c, lane, side) {
    const row = side === "you" ? this.you : this.leshy, other = side === "you" ? this.leshy : this.you;
    if (c.has("Fecundity") && side === "you") this.hand.push(Object.assign({}, c.spec));
    if (c.has("Rabbit Hole") && side === "you") this.hand.push(CM.cardSpec("Rabbit"));
    if (c.has("Dam Builder")) for (const j of [lane - 1, lane + 1]) if (j >= 0 && j < 4 && !row[j]) row[j] = new CM.CardCreature(CM.cardSpec("Dam"), side);
    if (!other[lane]) for (let j = 0; j < 4; j++) { const g = other[j]; if (g && g.has("Guardian") && !other[lane]) { other[lane] = g; other[j] = null; break; } }
  }
  died(c, lane, side, sacrificed = false) {
    if (side === "you") {
      this.bones += c.has("Bone King") ? 4 : 1;
      if (c.has("Unkillable") && c.name !== "Squirrel") { const s = Object.assign({}, c.spec); if (c.name === "Ouroboros") { s.power = (s.power || 0) + 1; s.health = (s.health || 0) + 1; } this.hand.push(s); }
      if (!sacrificed) for (let k = 0; k < this.hand.length; k++) if (CM.cardInfo(this.hand[k]).sigils.includes("Corpse Eater") && !this.you[lane]) { const h = this.hand.splice(k, 1)[0]; this.you[lane] = new CM.CardCreature(h, "you"); this.say("Corpse Maggots crawl into the empty place."); break; }
    }
    if (c.has("Steel Trap")) { const other = side === "leshy" ? this.you : this.leshy; if (other[lane]) { const v = other[lane]; other[lane] = null; this.died(v, lane, side === "leshy" ? "you" : "leshy"); this.say("The steel trap snaps shut."); } }
  }
  kill(side, lane) { const row = side === "you" ? this.you : this.leshy, c = row[lane]; if (!c) return; row[lane] = null; this.died(c, lane, side); }
  powerOf(side, lane) {
    const row = side === "you" ? this.you : this.leshy, other = side === "you" ? this.leshy : this.you, c = row[lane]; if (!c) return 0;
    let p = c.basePower; for (const j of [lane - 1, lane + 1]) if (j >= 0 && j < 4 && row[j] && row[j].has("Leader")) p += 1;
    if (other[lane] && other[lane].has("Stinky")) p -= 1;
    return Math.max(0, p);
  }
  *strike(side, lane) {
    const row = side === "you" ? this.you : this.leshy, other = side === "you" ? this.leshy : this.you, c = row[lane]; if (!c) return;
    let lanes = [lane]; if (c.has("All Lanes")) lanes = [0, 1, 2, 3]; else if (c.has("Trifurcated Strike")) lanes = [lane - 1, lane, lane + 1]; else if (c.has("Bifurcated Strike")) lanes = [lane - 1, lane + 1];
    for (const t of lanes) {
      if (t < 0 || t > 3 || row[lane] !== c) continue;
      const power = this.powerOf(side, lane); if (power <= 0) continue;
      let target = other[t];
      if (!target) for (let j = 0; j < 4; j++) { const b = other[j]; if (b && b.has("Burrower") && !other[t]) { other[t] = b; other[j] = null; target = b; break; } }
      const flying = c.has("Airborne") && !(target && target.has("Mighty Leap"));
      if (!target || flying || target.has("Waterborne")) { this.scale += side === "you" ? power : -power; yield { kind: "face", side, lane, t, power }; if (Math.abs(this.scale) >= 5 && !this.moonGuard()) return; continue; }
      target.health -= power; yield { kind: "hit", side, lane, t, power };
      if (target.has("Sharp Quills")) c.health -= 1;
      if (target.has("Bees Within") && target.owner === "you") this.hand.push(CM.cardSpec("Bee"));
      if (target.health <= 0 || (c.has("Touch of Death") && target.name !== "The Moon")) for (let j = 0; j < 4; j++) if (other[j] === target) this.kill(side === "you" ? "leshy" : "you", j);
      if (c.health <= 0) { this.kill(side, lane); return; }
    }
  }
  moonGuard() { return this.leshy.some((c) => c && c.name === "The Moon"); }
  *ringBell() {
    if (this.over) return;
    for (let lane = 0; lane < 4; lane++) { yield* this.strike("you", lane); if (this.check()) return; }
    this.endOfTurn("you"); yield { kind: "leshy_turn" };
    for (let lane = 0; lane < 4; lane++) if (this.queue[lane] && !this.leshy[lane]) { this.leshy[lane] = this.queue[lane]; this.queue[lane] = null; this.onPlay(this.leshy[lane], lane, "leshy"); yield { kind: "advance", lane }; }
    this.turn += 1; this.leshyTurnPlays(this.turn);
    yield* this.bossTrick();
    if (this.turn >= 30) { this.scale -= 1; this.say("The cold creeps in. Leshy grows impatient."); yield { kind: "face", side: "leshy", lane: 0, t: 0, power: 1 }; if (this.check()) return; }
    for (let lane = 0; lane < 4; lane++) {
      if (this.rising) { this.rising = false; this.say("The Moon hangs in the sky, gathering itself."); break; }
      yield* this.strike("leshy", lane); if (this.check()) return;
      if (this.leshy[lane] && this.leshy[lane].has("All Lanes")) break;
    }
    this.endOfTurn("leshy");
    for (const row of [this.you, this.leshy]) row.forEach((c, i) => { if (!c) return; c.turns += 1; if (c.has("Fledgling") && c.turns >= 1 && CM.CARD_GROWS[c.name]) row[i] = new CM.CardCreature(CM.cardSpec(CM.CARD_GROWS[c.name], { power: c.spec.power || 0, health: c.spec.health || 0 }), c.owner); });
    this.drawn = !(this.deck.length || this.squirrels > 0);
    yield { kind: "your_turn" };
  }
  endOfTurn(side) {
    const row = side === "you" ? this.you : this.leshy, moved = new Set();
    for (let i = 0; i < 4; i++) {
      const c = row[i]; if (!c || moved.has(c) || !c.has("Sprinter")) continue;
      let j = i + c.direction; if (j < 0 || j > 3 || row[j]) { c.direction = -c.direction; j = i + c.direction; }
      if (j >= 0 && j < 4 && !row[j]) { row[j] = c; row[i] = null; moved.add(c); }
    }
  }
  check() {
    const moon = this.moonGuard();
    if (this.boss === "Leshy" && this.phase === 2 && !moon) { this.over = "won"; return true; }
    if (this.scale >= 5 && !moon) { this.over = this.boss && this.phase === 1 ? "phase" : "won"; return true; }
    if (this.scale <= -5) { this.over = "lost"; return true; }
    return false;
  }
  *bossTrick() {
    const b = this.boss; if (!b || this.tricks >= (this.phase === 1 ? 1 : 2) || this.turn < 4 + this.tricks * 3) return;
    const mine = [0, 1, 2, 3].filter((i) => this.you[i] && this.you[i].name !== "Gold Nugget");
    if (b === "The Prospector" && mine.length) { this.tricks += 1; const i = mine.sort((a, c) => this.powerOf("you", c) - this.powerOf("you", a))[0]; this.you[i] = new CM.CardCreature(CM.cardSpec("Gold Nugget"), "you"); this.say("\"GOLD!\" The Prospector's pickaxe turns your creature to gold."); yield { kind: "trick", boss: b }; }
    else if (b === "The Angler" && mine.length) { const i = mine.sort((a, c) => this.powerOf("you", c) - this.powerOf("you", a))[0]; if (!this.leshy[i]) { this.tricks += 1; this.leshy[i] = this.you[i]; this.you[i] = null; this.leshy[i].owner = "leshy"; this.say("The Angler's hook drags your creature to his side."); yield { kind: "trick", boss: b }; } }
    else if (b === "The Trapper") { const free = [0, 1, 2, 3].filter((i) => !this.leshy[i]); if (free.length) { this.tricks += 1; this.leshy[free[0]] = new CM.CardCreature(CM.cardSpec("Steel Trap"), "leshy"); this.say("The Trapper sets his steel traps."); yield { kind: "trick", boss: b }; } }
    else if (b === "Leshy" && this.phase === 1 && mine.length && this.turn >= 6) { this.tricks += 1; const i = this.rng.pick(mine); this.you[i] = new CM.CardCreature(CM.cardSpec("Gold Nugget"), "you"); this.say("Leshy wears the Prospector's mask for a moment. \"Gold.\""); yield { kind: "trick", boss: b }; }
  }
  nextPhase() {
    this.phase = 2; this.scale = 0; this.tricks = 0; this.over = null; this.leshy = [null, null, null, null]; this.queue = [null, null, null, null];
    if (this.boss === "Leshy") { const moon = new CM.CardCreature(CM.cardSpec("The Moon"), "leshy"); this.leshy = [moon, moon, moon, moon]; this.rising = true; this.plan = []; this.hand.push(CM.cardSpec("Squirrel"), CM.cardSpec("Squirrel")); this.say("\"Behold... the Moon.\" Two squirrels scurry to your side."); }
    else { this.plan = this.makePlan(); this.leshyTurnPlays(this.turn); this.say(`${this.boss} takes off his mask... no. He puts on another.`); }
  }
};
