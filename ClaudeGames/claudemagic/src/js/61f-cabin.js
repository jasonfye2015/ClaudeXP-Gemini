"use strict";
// The cabin in the Wood (the thirteenth update): a log cabin in a clearing between the river and the fields, a path
// north to it from the road, smoke from its chimney, and inside, at a candlelit table, Leshy - the card master - who
// will play Claudescryption with anyone who sits down (64h-cards.js has the rules). A portal in the portal yard by the
// shaft comes here, and one by the cabin's door goes back. For now a game lost costs nothing; a game won pays gold, a
// card of the winner's choosing, and against his masks a thing besides. The collection and the deck are kept between
// runs in the village store (village.cards), and the deck is changed between games at the table.
CM.CABIN = { cells: [30, 14, 34, 16], door: [32, 16], front: [32, 17], path: [32, 18, 32, 29], clearing: [26, 10, 38, 22], portal: [29, 18], centre: [32, 15] };
CM.PORTAL_YARD.cabin = CM.PORTAL_YARD.plinths[0];                      // the first plinth lights for the cabin
CM.CARD_DECK_MIN = 4;
CM.CARD_DECK_MAX = 20;
// Leshy's games: where in his woods the cards are drawn from, how hard, what it pays, and what must be won first
CM.CARD_TABLES = [
  { id: "woods", name: "A game in the Woodlands", region: 0, difficulty: 0, gold: 25, pick: "common" },
  { id: "wet", name: "A game in the Wetlands", region: 1, difficulty: 1, gold: 45, pick: "common", needs: ["woods"] },
  { id: "snow", name: "A game on the Snow Line", region: 2, difficulty: 2, gold: 70, pick: "common", needs: ["wet"] },
  { id: "prospector", name: "Leshy wears the Prospector's mask", region: 0, difficulty: 1, boss: "The Prospector", gold: 110, pick: "rare", item: true, needs: ["woods"] },
  { id: "angler", name: "Leshy wears the Angler's mask", region: 1, difficulty: 2, boss: "The Angler", gold: 150, pick: "rare", item: true, needs: ["wet"] },
  { id: "trapper", name: "Leshy wears the Trapper's mask", region: 2, difficulty: 2, boss: "The Trapper", gold: 190, pick: "rare", item: true, needs: ["snow"] },
  { id: "leshy", name: "Leshy, unmasked - and the Moon", region: 2, difficulty: 3, boss: "Leshy", gold: 400, pick: "rare", item: true, needs: ["prospector", "angler", "trapper"] },
];
CM.LESHY_LINES = {
  greet: "The cabin smells of pine smoke and old paper. Behind the table, past the candles, two eyes catch the light. \"Sit,\" says Leshy. \"Let us play a game.\"",
  win: ["\"Hm. Well played.\"", "\"The cards favoured you. This time.\"", "\"You learn quickly. I do not like that.\""],
  lose: ["\"The scale tips my way. Come back when you have learned something.\"", "\"A pity. Sit again whenever you like.\"", "\"Your creatures are scattered. Collect yourself, and play again.\""],
};
CM.isCabinCell = (x, y) => x >= CM.CABIN.cells[0] && x <= CM.CABIN.cells[2] && y >= CM.CABIN.cells[1] && y <= CM.CABIN.cells[3];

// laid on the land after everything else (as the Mage Tower's clearing is): nothing the seed placed moves
CM.layCabin = function (fl) {
  const C = CM.CABIN, [x0, y0, x1, y1] = C.clearing, key = (x, y) => `${x},${y}`, [cx, cy] = C.centre;
  const open = (x, y, g) => { fl.grid[y][x] = 0; if (fl.kinds) delete fl.kinds[key(x, y)]; (fl.ground = fl.ground || {})[key(x, y)] = g; };
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (((x - cx) / 5.6) ** 2 + ((y - cy - 1) / 5.2) ** 2 <= 1 && !CM.isCabinCell(x, y)) open(x, y, (x * 7 + y * 3) % 5 ? "grass" : "litter");
  for (let y = C.cells[1]; y <= C.cells[3]; y++) for (let x = C.cells[0]; x <= C.cells[2]; x++) { fl.grid[y][x] = 1; (fl.kinds = fl.kinds || {})[key(x, y)] = x === C.door[0] && y === C.door[1] ? "cabindoor" : "cabin"; if (fl.ground) delete fl.ground[key(x, y)]; }
  const [px, py0, , py1] = C.path; for (let y = py0; y <= py1; y++) { open(px, y, "dirt"); if (!(fl.seen || []).some(([sx, sy]) => sx === px && sy === y)) (fl.seen = fl.seen || []).push([px, y]); }   // (the path is on the map from the road)
  fl.things[key(...C.front)] = { type: "cabin" };
  fl.things[key(...C.portal)] = { type: "portal", to: "town" };
  fl.rooms = (fl.rooms || []).concat({ x0, y0, x1, y1, name: "Leshy's cabin" });
  for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) if (!(fl.seen || []).some(([sx, sy]) => sx === x && sy === y)) (fl.seen = fl.seen || []).push([x, y]);
  return fl;
};

CM.CARD_FIND = { chest: 1 / 22, champion: 1 / 4, towerBoss: 1 / 3 };     // the odds of a card: in a chest, on a champion, from a tower boss
Object.assign(CM.Game.prototype, {
  // a card found: by a hash of the run's seed and the place (never the floor's own dice), at the odds given
  findCard(where, odds, rarity, why) {
    const h = CM.hashSeed(`${this.seed}:cardfind:${where}`);
    if ((h % 10000) / 10000 >= odds) return null;
    const pool = rarity === "rare" ? CM.CARD_RARES : CM.CARD_COMMONS, name = pool[Math.floor(h / 10000) % pool.length];
    this.addCard(name, why); this.tally.cardsFound = (this.tally.cardsFound || 0) + 1;
    return name;
  },
  // the collection and the deck, kept with the village
  cards() {
    this.village = this.village || {};
    const K = this.village.cards = this.village.cards || {};
    if (!K.owned) { K.owned = {}; for (const n of CM.CARD_STARTER) K.owned[n] = (K.owned[n] || 0) + 1; }
    if (!K.deck) K.deck = CM.CARD_STARTER.slice();
    K.beaten = K.beaten || {}; K.games = K.games || 0; K.wins = K.wins || 0; K.found = K.found || 0;
    return K;
  },
  saveCards() { if (this.saveVillage) this.saveVillage(); },
  // a card found (a chest, a boss, a reward): into the box at the cabin
  addCard(name, why) {
    if (!CM.CARDS[name]) return false;
    const K = this.cards(); K.owned[name] = (K.owned[name] || 0) + 1; K.found += why === "reward" ? 0 : 1;
    if (K.deck.length < 8 && why !== "reward") K.deck.push(name);         // (a small deck takes a new card at once)
    this.saveCards();
    if (why && why !== "reward") this.say(`${why} A Claudescryption card: ${CM.CARDS[name][0]} ${name}. It goes to the box in Leshy's cabin.`);
    return true;
  },
  // the deck: a card in (if one is free in the box) or out (keeping at least the least a deck may be)
  deckAdd(name) {
    const K = this.cards(), inDeck = K.deck.filter((n) => n === name).length;
    if (!K.owned[name] || inDeck >= K.owned[name]) return "There is no other copy of that card in the box.";
    if (K.deck.length >= CM.CARD_DECK_MAX) return `A deck holds ${CM.CARD_DECK_MAX} cards at most.`;
    K.deck.push(name); this.saveCards(); return "";
  },
  deckRemove(name) {
    const K = this.cards(), i = K.deck.indexOf(name);
    if (i < 0) return "That card is not in the deck.";
    if (K.deck.length <= CM.CARD_DECK_MIN) return `A deck needs ${CM.CARD_DECK_MIN} cards at least.`;
    K.deck.splice(i, 1); this.saveCards(); return "";
  },
  cardTableOpen(T) { const K = this.cards(); return !T.needs || T.needs.every((id) => K.beaten[id]); },
  // sit down to a game
  startCardGame(id) {
    const T = CM.CARD_TABLES.find((t) => t.id === id), K = this.cards();
    if (!T) return "No such game.";
    if (!this.cardTableOpen(T)) return "Leshy shakes his head. \"Not yet. Win the games before it.\"";
    if (K.deck.length < CM.CARD_DECK_MIN) return `A deck needs ${CM.CARD_DECK_MIN} cards at least.`;
    K.games += 1; this.saveCards();
    const seed = CM.hashSeed(`${this.seed}:cards:${K.games}:${id}`);
    this.cardGame = { id, table: T, battle: new CM.CardBattle(K.deck.map((n) => CM.cardSpec(n)), T.region, T.difficulty, T.boss || null, seed), reward: null };
    return "";
  },
  // the game over: a win pays (gold now, a card to choose, a thing against a mask); a loss costs nothing
  finishCardGame() {
    const G = this.cardGame; if (!G || !G.battle.over || G.done) return null;
    G.done = true; const T = G.table, K = this.cards(), rnd = new CM.Random(CM.hashSeed(`${this.seed}:cardreward:${K.games}`));
    if (G.battle.over !== "won") { this.say(`Leshy: ${rnd.pick(CM.LESHY_LINES.lose)}`); return { won: false }; }
    K.wins += 1; const first = !K.beaten[T.id]; K.beaten[T.id] = (K.beaten[T.id] || 0) + 1;
    const gold = first ? T.gold * 2 : T.gold; this.gold += gold;
    const pool = T.pick === "rare" ? CM.CARD_RARES.concat(CM.CARD_COMMONS.filter((n) => CM.CARDS[n][1] >= 2 || CM.CARDS[n][2] >= 5)) : CM.CARD_COMMONS, choices = [];
    while (choices.length < 3) { const n = rnd.pick(pool); if (!choices.includes(n)) choices.push(n); }
    if (T.pick === "rare" && !choices.some((n) => CM.CARD_RARES.includes(n))) choices[0] = rnd.pick(CM.CARD_RARES);
    let item = null;
    if (T.item) { const depth = Math.max(4, ...(this.trail || []).map((t) => t[0] || 0)); item = CM.affix(CM.makeItem(depth + 2, rnd), depth + 4, rnd); item.unknown = false; this.gain([item], "cards"); }
    G.reward = { gold, choices, item };
    this.tally.cardWins = (this.tally.cardWins || 0) + 1;
    if (T.id === "leshy") this.achieve("moon");
    this.saveCards(); this.saveRun();
    this.say(`Leshy: ${rnd.pick(CM.LESHY_LINES.win)} (${gold} gold${first ? ", the first time doubled" : ""}${item ? `, and ${item.name}` : ""}.)`);
    return { won: true, gold, choices, item };
  },
  takeCardReward(name) { const G = this.cardGame; if (!G || !G.reward || G.reward.taken || !G.reward.choices.includes(name)) return false; G.reward.taken = name; this.addCard(name, "reward"); this.say(`Leshy slides a card across the table: ${CM.CARDS[name][0]} ${name}.`); return true; },
  leaveCardTable() { this.cardGame = null; },
});
