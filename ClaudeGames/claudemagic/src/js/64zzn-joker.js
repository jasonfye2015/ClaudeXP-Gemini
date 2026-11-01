"use strict";
// The party's standing with the Joker (v16.8): JXP - Joker experience - earned by play anywhere on the floor (gold
// laid, tickets won, levels reached at the cabinets, places on the boards and records, quests done, tournament
// nights settled, high-rollers beaten), and with it the Joker level, from 1 to 50, kept with the floor's books so it
// carries from expedition to expedition. Each level owes something (gold, and a card every fifth), collected on the
// standing page with the bonus tickets the level has banked, and
// the level itself is worth something in and out of the Joker:
//   on the floor - tickets: 1% more for each level past the first (to 30%), banked as they're won; the prize counter: 2% more off at every sixth level (to 10%)
//   out in the world - fights pay 1% more gold for each level past the fourth (to 20%); heroes learn 5% more from
//   fights at level 10, 10% at 20, 15% at 30, 20% at 40; and every expedition starts with a Joker's Cordial in the
//   pack from level 8 (two from 18, three from 28).
// The window is 76zzr-joker.js; fights read jkMul in 62-combat.js.
{ const JK = CM.JK = { cap: 50, stakePer: 10, stakeMax: 50, ticketPer: 4, level: 3, board: 10, record: 25, quest: 40, tour: 30, tourTop: 60, roller: 80 };
  JK.need = (L) => Math.round(80 * Math.pow(L, 1.45));   // JXP from level L to L + 1
  JK.at = (jxp) => { let L = 1, left = jxp; while (L < JK.cap && left >= JK.need(L)) { left -= JK.need(L); L += 1; } return { level: L, into: left, need: L < JK.cap ? JK.need(L) : 0 }; };
  JK.tickets = (L) => Math.min(30, L - 1) / 100;
  JK.counter = (L) => Math.min(10, Math.floor(L / 6) * 2) / 100;
  JK.gold = (L) => Math.min(20, Math.max(0, L - 4)) / 100;
  JK.xp = (L) => Math.min(20, Math.floor(L / 10) * 5) / 100;
  JK.cordials = (L) => (L >= 28 ? 3 : L >= 18 ? 2 : L >= 8 ? 1 : 0);
  JK.PERKS = [[2, "Bonus tickets: 1% more for each Joker level past the first, up to 30% (banked; collect them here)"], [5, "Fights pay 1% more gold for each level past the fourth, up to 20%"], [6, "The prize counter: 2% more off (4% at 12, up to 10% at 30)"],
    [8, "A Joker's Cordial in the pack at the start of every expedition (two at 18, three at 28)"], [10, "Heroes learn 5% more from fights (10% at 20, 15% at 30, 20% at 40)"]];
  JK.reward = (L) => ({ gold: 20 * L, card: L % 5 === 0 ? (L >= 25 ? "rare" : L >= 15 ? "better" : "common") : null });
  const cordial = (L) => ({ name: "The Joker's Cordial", kind: "heal", power: 30 + L * 2, value: 30 });
  const P = CM.Game.prototype, st0 = P.cgStake, tk0 = P.tkAdd, rec0 = P.cgRecord, q0 = P.flQuestCollect, tour0 = P.flTourSettle, hr0 = P.hrSettle, fp0 = P.flPrice, new0 = P.newGame;
  Object.assign(P, {
    jkStore() { const F = this.cgStore(); F.jk = F.jk || { jxp: 0, level: 1, bank: 0, owed: [], by: {}, tk: 0 }; return F.jk; },
    jkLevel() { return this.jkStore().level; },
    jkInfo() { const J = this.jkStore(); return Object.assign(JK.at(J.jxp), { jxp: J.jxp }); },
    // JXP earned; each level gained is owed its reward, to collect
    jkGain(n, why) { n = Math.floor(n); if (n <= 0) return []; const J = this.jkStore(), was = J.level; J.jxp += n; J.by[why || "play"] = (J.by[why || "play"] || 0) + n; const now = JK.at(J.jxp).level, ups = [];
      for (let L = was + 1; L <= now; L++) { ups.push(L); J.owed.push(L); } J.level = now;
      if (ups.length) { (this.jkUps = this.jkUps || []).push(...ups); this.cgCelebrate && this.cgCelebrate(ups.some((L) => L % 5 === 0) ? 2 : 1, `Joker level ${now}!`); } return ups; },
    jkWaiting() { const J = this.jkStore(); return { levels: J.owed.slice(), tickets: Math.floor(J.bank) }; },
    // the levels' rewards and the banked tickets, collected
    jkCollect() { const J = this.jkStore(), out = { gold: 0, tickets: Math.floor(J.bank), cards: [], levels: J.owed.slice() };
      for (const L of J.owed) { const R = JK.reward(L); out.gold += R.gold; if (R.card && this.cgTierCard) { const c = this.cgTierCard(R.card, `Joker level ${L}!`, new CM.Random(CM.hashSeed(`${this.seed}:jk:${L}`))); if (c) out.cards.push(c); } }
      J.owed = []; this.gold += out.gold; if (out.tickets) { J.bank -= out.tickets; tk0.call(this, out.tickets, "joker"); } this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out; },
    // a multiplier out in the world: "gold" from fights, "xp" from fights
    jkMul(kind) { const L = this.jkLevel ? this.jkLevel() : 1; return 1 + (kind === "gold" ? JK.gold(L) : kind === "xp" ? JK.xp(L) : 0); },
    cgStake(game, bet) { const why = st0.call(this, game, bet); if (!why) { const J = this.jkStore(); J.sf = (J.sf || 0) + Math.min(JK.stakeMax, Math.floor(bet) / JK.stakePer); const n = Math.floor(J.sf + 1e-9); J.sf -= n; this.jkGain(n, game); } return why; },   // (a part of a JXP carries: small stakes add up, and don't count for more)
    tkAdd(n, why) { const k = tk0.call(this, n, why); if (k > 0 && why !== "joker") { const J = this.jkStore(); J.bank += k * JK.tickets(J.level); J.tk += k; const g = Math.floor(J.tk / JK.ticketPer); J.tk -= g * JK.ticketPer; this.jkGain(g, why); } return k; },
    cgRecord(table, score, level) { const F = this.cgStore(), before = F.records || 0, r = rec0.call(this, table, score, level); let n = (CM.FAIR && CM.FAIR[table]) || table === "bingo" ? 0 : (level || 0) * JK.level;   // (only a cabinet's levels are levels: bingo sends its balls, the fairground its hundreds)
      if (r > 0) n += JK.board; if ((F.records || 0) > before) n += JK.record; this.jkGain(n, table); return r; },
    flQuestCollect(i) { const out = q0.call(this, i); if (out && !out.error) this.jkGain(JK.quest, "quests"); return out; },
    flTourSettle() { const N = this.flTour(), done = !!N.settled, out = tour0.call(this); if (!done && out && !out.error) this.jkGain(out.place <= 3 ? JK.tourTop : JK.tour, "tournament"); return out; },
    hrSettle(win, detail) { const out = hr0.call(this, win, detail); if (out && win) this.jkGain(JK.roller, "highroller"); return out; },
    flPrice(id, cost) { const c = fp0.call(this, id, cost); return Math.max(1, Math.round(c * (1 - JK.counter(this.jkLevel())))); },
    // a new expedition: the Joker's cordials in the pack
    newGame(...a) { const out = new0.apply(this, a); try { const L = this.cgStore && this.jkLevel(), n = L ? JK.cordials(L) : 0; for (let k = 0; k < n; k++) this.bag.push(cordial(L)); } catch (e) { /* no books yet */ } return out; },
  });
}
