"use strict";
// Practice (v17.0): any table that takes a stake can be played for nothing - no gold laid, none paid, no tickets, no
// cards, no JXP, nothing on the boards, the jackpot and the quests untouched - to learn it. The party's purse and the
// floor's whole books (tickets, bait, balls, seats, the creel book...) are put back exactly as they were when practice
// ends, whatever happened. The tables with nothing to practise (the free ones, the daily wheel, the lottery's draw,
// the idle works) don't offer it. The window is 76zzt-howto.js.
{ const PR = CM.PRACTICE = { NONE: ["lottery", "prizewheel", "mint", "shelter", "mahjong", "lexicon", "conduit", "patience", "traps", "vault"] };
  PR.can = (id) => !PR.NONE.includes(id);
  const P = CM.Game.prototype, st0 = P.cgStake, pay0 = P.cgPay, tk0 = P.tkAdd, card0 = P.cgCard, tier0 = P.cgTierCard, rec0 = P.cgRecord, hr0 = P.hrSettle, jk0 = P.jkGain, cel0 = P.cgCelebrate;
  Object.assign(P, {
    prOn() { return !!this.cgPractice; },
    // the whole of the floor's books is kept at the start and put back at the end: bait, balls, seats, boards, all
    prStart(id) { if (!PR.can(id)) return { error: "There's nothing to practise here - it's free." }; this.cgStore(); this.cgPractice = { id, gold: this.gold, books: JSON.stringify(this.casino()) }; return this.cgPractice; },
    prEnd() { const S = this.cgPractice; if (!S) return null; this.cgPractice = null; this.gold = S.gold; this.village.casino = JSON.parse(S.books); this.arcLive = {}; this.saveCasino && this.saveCasino(); return S; },
    cgStake(game, bet) { if (this.cgPractice) { bet = Math.floor(Number(bet) || 0); return bet < 1 ? "Put a chip down first." : ""; } return st0.call(this, game, bet); },
    cgPay(game, amount) { if (this.cgPractice) return amount > 0 ? amount : 0; return pay0.call(this, game, amount); },
    tkAdd(n, why) { if (this.cgPractice) return n > 0 ? n : 0; return tk0.call(this, n, why); },
    cgCard(rare, why, rnd) { return this.cgPractice ? null : card0.call(this, rare, why, rnd); },
    cgTierCard(tier, why, R) { return this.cgPractice ? null : tier0.call(this, tier, why, R); },
    cgRecord(table, score, level) { return this.cgPractice ? 0 : rec0.call(this, table, score, level); },
    hrSettle(win, detail) { return this.cgPractice ? null : hr0.call(this, win, detail); },
    jkGain(n, why) { return this.cgPractice ? [] : jk0.call(this, n, why); },
    cgCelebrate(tier, text) { if (!this.cgPractice) cel0.call(this, tier, text); },
  });
}
