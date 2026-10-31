"use strict";
// The Joker's Club (the thirty-ninth big update - v14.9): three things that tie the floor together.
// - High-score boards: each scoring table keeps its ten best games - the score, how far it went, the day and who
//   played - and a score that beats the old best is a record broken.
// - The loyalty card: a stamp for each different table played (a stake laid, or a free table paying out); eight
//   different tables fill a card, which (collected) pays gold and a Claudescryption card; a fresh card starts. Cards filled raise
//   the membership - Bronze, Silver, Gold, Platinum - and the better the membership the better a full card's reward.
// - Achievements: bronze, silver and gold marks of what has been done on the floor, each paying once when collected -
//   gold, and from silver up a card too.
// The window is 76zf-floorclub.js.
CM.CLUB = {
  BOARDS: ["runestack", "manamine", "glimmer", "swarm", "hexmarch", "shatterpane", "starstone", "moatleap", "runestep", "pinball"],
  ARCADE: ["rsCards", "mmCards", "gzCards", "swCards", "hxCards", "pnCards", "sdCards", "mqCards", "rpCards"],
  keep: 10, stamps: 8,
  TIERS: [["Guest", 0], ["Bronze", 1], ["Silver", 3], ["Gold", 6], ["Platinum", 10]],
  REWARD: { bronze: { gold: 100 }, silver: { gold: 400, card: "common" }, gold: { gold: 1500, card: "rare" } },
};
const CLUB = CM.CLUB;
CLUB.levelIn = (F, key) => Object.keys(F[key] || {}).filter((k) => F[key][k]).reduce((m, k) => Math.max(m, Number(k) || 0), 0);
CLUB.arcadeBest = (F) => Math.max(0, ...CLUB.ARCADE.map((k) => CLUB.levelIn(F, k)));
CLUB.arcadeAt = (F, n) => CLUB.ARCADE.filter((k) => CLUB.levelIn(F, k) >= n).length;
CLUB.sum = (o) => Object.values(o || {}).reduce((a, b) => a + b, 0);
CLUB.tables = (F) => Object.keys((F.loyalty || {}).all || {}).length;
CLUB.onBoards = (F) => Object.values(F.boards || {}).filter((b) => b.length).length;
CLUB.member = (done) => { let t = CLUB.TIERS[0]; for (const x of CLUB.TIERS) if (done >= x[1]) t = x; return t[0]; };
CLUB.ACH = [
  ["first", "bronze", "First Chip", "Play any table.", (F) => CLUB.tables(F) >= 1],
  ["tables5", "bronze", "Floor Walker", "Play five different tables.", (F) => CLUB.tables(F) >= 5],
  ["card1", "bronze", "Lucky Card", "Win a card on the floor.", (F) => (F.cards || []).length >= 1],
  ["claw1", "bronze", "Got One!", "Win a prize from the Wishing Claw.", (F) => (F.clawPrizes || 0) >= 1],
  ["board1", "bronze", "On the Board", "Put a score on a high-score board.", (F) => CLUB.onBoards(F) >= 1],
  ["loyal1", "bronze", "Stamped", "Fill a loyalty card.", (F) => ((F.loyalty || {}).done || 0) >= 1],
  ["won1k", "bronze", "In the Black", "Be paid 1,000 gold by the floor, all told.", (F) => CLUB.sum(F.paid) >= 1000],
  ["arcade5", "bronze", "Arcade Regular", "Reach level 5 on an arcade table.", (F) => CLUB.arcadeBest(F) >= 5],
  ["tables15", "silver", "Grand Tour", "Play fifteen different tables.", (F) => CLUB.tables(F) >= 15],
  ["card10", "silver", "Card Shark", "Win ten cards on the floor.", (F) => (F.cards || []).length >= 10],
  ["jackpot", "silver", "Jackpot!", "Hit the Gilded Reels' jackpot.", (F) => (F.jackpots || 0) >= 1],
  ["claw10", "silver", "Claw Master", "Win ten prizes from the Wishing Claw.", (F) => (F.clawPrizes || 0) >= 10],
  ["boards5", "silver", "Scoreboard Regular", "Be on five different high-score boards.", (F) => CLUB.onBoards(F) >= 5],
  ["records3", "silver", "Record Breaker", "Beat your own best score three times.", (F) => (F.records || 0) >= 3],
  ["silver", "silver", "Silver Member", "Reach Silver membership.", (F) => ((F.loyalty || {}).done || 0) >= 3],
  ["won10k", "silver", "Well Off", "Be paid 10,000 gold by the floor, all told.", (F) => CLUB.sum(F.paid) >= 10000],
  ["arcade10", "silver", "Arcade Ace", "Reach level 10 on an arcade table.", (F) => CLUB.arcadeBest(F) >= 10],
  ["pinball100k", "silver", "Wizard of the Wyrmhold", "Score 100,000 at Wyrmhold Pinball.", (F) => (F.pbBest || 0) >= 100000],
  ["tables25", "gold", "Every Table", "Play twenty-five different tables.", (F) => CLUB.tables(F) >= 25],
  ["card30", "gold", "The Full Deck", "Win thirty cards on the floor.", (F) => (F.cards || []).length >= 30],
  ["gold", "gold", "Gold Member", "Reach Gold membership.", (F) => ((F.loyalty || {}).done || 0) >= 6],
  ["platinum", "gold", "Platinum Member", "Reach Platinum membership.", (F) => ((F.loyalty || {}).done || 0) >= 10],
  ["won100k", "gold", "High Roller", "Be paid 100,000 gold by the floor, all told.", (F) => CLUB.sum(F.paid) >= 100000],
  ["arcade6", "gold", "Arcade Polymath", "Reach level 5 on six different arcade tables.", (F) => CLUB.arcadeAt(F, 5) >= 6],
  ["boards10", "gold", "Hall of Champions", "Be on every high-score board.", (F) => CLUB.onBoards(F) >= CLUB.BOARDS.length],
  ["pinball500k", "gold", "The Dragon's Bane", "Score 500,000 at Wyrmhold Pinball.", (F) => (F.pbBest || 0) >= 500000],
];
{ const stake0 = CM.Game.prototype.cgStake, pay0 = CM.Game.prototype.cgPay;
  Object.assign(CM.Game.prototype, {
    cgStake(game, bet) { const why = stake0.call(this, game, bet); if (!why) { this.cgStamp(game); this.cgAchieve(); } return why; },
    cgPay(game, amount) { const n = pay0.call(this, game, amount); if (n > 0) { this.cgStamp(game); this.cgAchieve(); } return n; },
    cgNews() { const F = this.cgStore(); F.news = F.news || []; return F.news; },
    // a high-score board: the ten best, and whether this one is a record
    cgRecord(table, score, level) {
      if (!(score > 0)) return 0; const F = this.cgStore(); F.boards = F.boards || {}; const B = F.boards[table] = F.boards[table] || [], best = B.length ? B[0].score : 0;
      const who = (this.party && this.party[0] && this.party[0].name) || "The party", e = { score: Math.floor(score), level: level || 0, at: CM.today ? CM.today() : "", who };
      B.push(e); B.sort((a, b) => b.score - a.score); B.length = Math.min(B.length, CLUB.keep); const rank = B.indexOf(e) + 1;
      if (rank === 1 && best > 0 && score > best) { F.records = (F.records || 0) + 1; this.cgNews().push({ kind: "record", table, score: e.score }); }
      else if (rank > 0) this.cgNews().push({ kind: "board", table, score: e.score, rank });
      this.cgAchieve(); return rank;
    },
    // the loyalty card: a stamp for a table not yet on this card; eight make a full card
    cgStamp(table) {
      const F = this.cgStore(), L = F.loyalty = F.loyalty || { card: [], done: 0, all: {} }; L.all[table] = (L.all[table] || 0) + 1;
      if (L.card.includes(table)) return false; L.card.push(table); this.cgNews().push({ kind: "stamp", table, n: L.card.length });
      if (L.card.length >= CLUB.stamps) { L.done += 1; L.card = []; L.unpaid = (L.unpaid || 0) + 1; this.cgNews().push({ kind: "loyalty", done: L.done, member: CLUB.member(L.done) }); }
      return true;
    },
    // achievements: each checked against the floor's records, paid once
    cgAchieve() {
      const F = this.cgStore(), A = F.ach = F.ach || {}; let any = false;
      for (const [id, tier, name, , check] of CLUB.ACH) { if (A[id] || !check(F, this)) continue; A[id] = { at: CM.today ? CM.today() : "", paid: false }; any = true; this.cgNews().push({ kind: "ach", id, tier, name }); }
      if (any) { this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); } return any;
    },
    // what is waiting to be collected, and collecting it: an achievement's reward, or a full loyalty card's
    cgUnpaid() { const F = this.cgStore(), A = F.ach || {}, L = F.loyalty || {}; return { ach: CLUB.ACH.filter(([id]) => A[id] && !A[id].paid).map(([id]) => id), loyalty: L.unpaid || 0 }; },
    cgCollect(what) {
      const F = this.cgStore(), out = { gold: 0, cards: [] };
      if (what === "loyalty") { const L = F.loyalty || {}; if (!L.unpaid) return out; const n = L.done - L.unpaid + 1, member = CLUB.member(n), k = CLUB.TIERS.findIndex((t) => t[0] === member); L.unpaid -= 1;
        out.gold = 150 + 100 * k; const card = this.cgTierCard(k >= 4 ? "rare" : k >= 3 ? "better" : "common", `A full loyalty card at the Gilded Joker (${member} member).`, new CM.Random(CM.hashSeed(`${this.seed}:loyalty:${n}`))); if (card) out.cards.push(card); }
      else { const row = CLUB.ACH.find(([id]) => id === what), A = F.ach || {}; if (!row || !A[what] || A[what].paid) return out; const R = CLUB.REWARD[row[1]]; A[what].paid = true; out.gold = R.gold;
        if (R.card) { const card = this.cgTierCard(R.card, `The Gilded Joker's achievement: ${row[2]}.`, new CM.Random(CM.hashSeed(`${this.seed}:ach:${what}`))); if (card) out.cards.push(card); } }
      this.gold += out.gold; F.clubGold = (F.clubGold || 0) + out.gold; this.cgAchieve(); this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out;
    },
  });
}
