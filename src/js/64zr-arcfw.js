"use strict";
// The arcade cabinets' common works (the forty-second big update - v15.6). Each level-by-level cabinet on the Gilded
// Joker's floor registers its rules here - a Level class (constructor(n, seed, keep), update(dt), events, stage of
// "play", "clear" or "over", score, lives) - and gets the same house terms as the rest of the arcade: one stake a game;
// each level cleared pays gold (more for each level, every game) and prize tickets (as many as the level's number);
// every third level a Claudescryption card, the first time ever (common to the fourth, a stronger common to the ninth,
// rare from the tenth); the game's end puts its score on the cabinet's high-score board. The window's side is
// 76zi-arcfw.js.
CM.ARC = { reg: {} };
CM.ARC.add = (id, def) => { def.id = id; def.pay = def.pay || ((n) => 0.05 + 0.03 * n); def.cardEvery = def.cardEvery || 3; def.keep = def.keep || ((L) => ({ score: L.score, lives: L.lives, extraGiven: L.extraGiven })); CM.ARC.reg[id] = def; if (CM.CLUB && !CM.CLUB.BOARDS.includes(id)) CM.CLUB.BOARDS.push(id); if (CM.DAILY && def.marks) CM.DAILY.MARKS[id] = def.marks; };
// a few things most cabinets want
CM.ARC.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
CM.ARC.near = (a, b, r) => Math.hypot(a.x - b.x, a.y - b.y) < r;
Object.assign(CM.Game.prototype, {
  arcState(id) { return this.cgStore()[`ar_${id}`] || null; },
  arcClaimed(id) { const F = this.cgStore(), k = `ar_${id}_cards`; F[k] = F[k] || {}; return F[k]; },
  arcLevel(id) {
    const S = this.arcState(id), def = CM.ARC.reg[id]; if (!S || S.stage !== "play") return null; const live = this.arcLive = this.arcLive || {}; let L = live[id];
    if (!L || L.key !== `${S.seed}:${S.n}`) {
      if (L && L.key && L.key.startsWith(`${S.seed}:`)) { L = live[id] = new def.Level(S.n, CM.hashSeed(`${S.seed}:${S.n}`), def.keep(L)); L.key = `${S.seed}:${S.n}`; }
      else { S.stage = "done"; S.last = S.last || { level: S.n, won: S.won, cards: [], lost: true }; this.saveCasino && this.saveCasino(); return null; }
    }
    return L;
  },
  arcStart(id, bet) {
    const S0 = this.arcState(id), def = CM.ARC.reg[id], live = this.arcLive = this.arcLive || {};
    if (S0 && S0.stage === "play" && live[id] && live[id].key && live[id].key.startsWith(`${S0.seed}:`)) return { error: "A game is on." };
    const why = this.cgStake(id, bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; const S = F[`ar_${id}`] = { stage: "play", n: 1, bet: Math.floor(bet), seed: `${this.seed}:${id}:${F.n}`, won: 0, cards: [] };
    live[id] = new def.Level(1, CM.hashSeed(`${S.seed}:1`)); live[id].key = `${S.seed}:1`; this.saveCasino && this.saveCasino(); return S;
  },
  // a level cleared: gold every game, tickets, a card each third level the first time; the end: the board
  arcCheck(id) {
    const S = this.arcState(id), L = (this.arcLive || {})[id], def = CM.ARC.reg[id]; if (!S || !L || S.stage !== "play") return null;
    if (L.stage === "clear") {
      const n = S.n, pay = Math.round(S.bet * def.pay(n)), C = this.arcClaimed(id); let card = null;
      if (n % def.cardEvery === 0 && !C[n]) { card = this.cgTierCard(CM.cardTierFor(n), `${def.name}, level ${n} cleared!`, new CM.Random(CM.hashSeed(`${this.seed}:${id}:card:${n}`))); C[n] = card || true; if (card) S.cards.push(card); }
      this.cgPay(id, pay); const tk = this.tkAdd ? this.tkAdd(n, id) : 0; S.won += pay; S.n += 1; this.saveCasino && this.saveCasino(); this.emit("change");
      this.arcLevel(id); return { cleared: n, pay, card, tickets: tk };
    }
    if (L.stage === "over") { S.stage = "done"; S.last = { level: S.n, score: L.score, won: S.won, cards: S.cards.slice() }; const F = this.cgStore(); F[`ar_${id}_best`] = Math.max(F[`ar_${id}_best`] || 0, L.score); this.cgRecord && this.cgRecord(id, L.score, S.n); this.arcLive[id] = null; this.saveCasino && this.saveCasino(); this.emit("change"); return { over: true }; }
    return null;
  },
});
