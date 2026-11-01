"use strict";
// The Daily Challenge (the fortieth big update - v15.0): each real day the Gilded Joker chalks one challenge on the
// board by the door - one of the ten scoring tables, picked by the date (so the same for every party that day), and how
// far to get in it: a bronze, a silver and a gold mark (the level reached, or for the pinball table the score marks
// passed; a little higher at the weekend). Any game of that table finished that day counts. Each mark reached pays
// once - collected like the club's rewards: gold for bronze, gold and a common card for silver, more gold and a
// stronger card for gold. Days in a row with at least the bronze mark make a streak, which adds a tenth to the
// challenge's gold for each day (up to double), and every seventh day of a streak brings a rare card. The last fortnight
// is kept, and a mark reached but not collected before midnight waits to be collected the next day. The window:
// 76zg-daily.js.
CM.DAILY = {
  // the marks by table: [bronze, silver, gold] - levels reached (the pinball table: score marks passed)
  MARKS: { runestack: [3, 5, 8], manamine: [2, 4, 6], glimmer: [2, 3, 5], swarm: [3, 5, 8], hexmarch: [2, 4, 6], shatterpane: [2, 3, 5], starstone: [3, 5, 8], moatleap: [2, 3, 5], runestep: [3, 5, 7], pinball: [3, 5, 7] },
  REWARD: [{ gold: 150 }, { gold: 400, card: "common" }, { gold: 900, card: "better" }], streakCard: 7, keep: 14,
};
const DAILY = CM.DAILY;
// the day as yyyy-mm-dd on the player's own clock
DAILY.key = (d) => { d = d || new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
DAILY.prev = (key) => { const [y, m, d] = key.split("-").map(Number), t = new Date(y, m - 1, d - 1); return DAILY.key(t); };
// what the house chalks up for a day: the same for everyone
DAILY.pick = (key) => { const R = new CM.Random(CM.hashSeed(`gilded-joker-daily:${key}`)), pool = CM.CLUB.BOARDS.filter((b) => DAILY.MARKS[b]), table = pool[R.int(0, pool.length - 1)], [y, m, d] = key.split("-").map(Number), wd = new Date(y, m - 1, d).getDay(), bump = wd === 0 || wd === 6 ? 1 : 0;
  return { day: key, table, marks: DAILY.MARKS[table].map((x) => x + bump), weekend: !!bump }; };
{ const rec0 = CM.Game.prototype.cgRecord;
  Object.assign(CM.Game.prototype, {
    cgRecord(table, score, level) { const r = rec0.call(this, table, score, level); this.dlCount(table, score, level); return r; },
    dlToday() { return this.dlDay || DAILY.key(); },
    // today's challenge, made fresh when the day has turned (and the day before put in the history)
    dlState() {
      const F = this.cgStore(), key = this.dlToday(); let D = F.daily;
      if (!D || D.day !== key) { const old = D; D = F.daily = { ...DAILY.pick(key), best: 0, score: 0, got: [false, false, false], paid: [false, false, false], streak: old ? old.streak || 0 : 0, lastDay: old ? old.lastDay || "" : "", history: old ? old.history || [] : [], streakPaid: old ? old.streakPaid || 0 : 0, streakUnpaid: old ? old.streakUnpaid || 0 : 0,
          carry: (old ? old.carry || [] : []).concat(old && old.got ? old.got.map((g, i) => (g && !old.paid[i] ? { day: old.day, i, mult: 1 + 0.1 * Math.min(10, Math.max(0, (old.streak || 1) - 1)) } : null)).filter(Boolean) : []) };
        if (old && old.day) { D.history.unshift({ day: old.day, table: old.table, best: old.best, marks: old.marks, got: old.got.filter(Boolean).length }); D.history.length = Math.min(D.history.length, DAILY.keep); }
        if (D.lastDay && D.lastDay !== DAILY.prev(key) && D.lastDay !== key) D.streak = 0; }
      return D;
    },
    // a game of today's table ended: how far it got, and the marks reached
    dlCount(table, score, level) {
      const D = this.dlState(); if (table !== D.table) return; D.best = Math.max(D.best, level || 0); D.score = Math.max(D.score, score || 0);
      D.marks.forEach((m, i) => { if (D.got[i] || D.best < m) return; D.got[i] = true; this.cgNews && this.cgNews().push({ kind: "daily", tier: i, mark: m, table });
        if (i === 0) { D.streak = D.lastDay === DAILY.prev(D.day) ? (D.streak || 0) + 1 : 1; D.lastDay = D.day; if (D.streak % DAILY.streakCard === 0) D.streakUnpaid = (D.streakUnpaid || 0) + 1; } });
      this.saveCasino && this.saveCasino();
    },
    dlMult() { const D = this.dlState(); return 1 + 0.1 * Math.min(10, Math.max(0, (D.streak || 1) - 1)); },
    dlCollect(what) {
      const D = this.dlState(), out = { gold: 0, cards: [] };
      if (what === "carry") { for (const c of D.carry || []) { const R = DAILY.REWARD[c.i], g = Math.round(R.gold * c.mult); out.gold += g; if (R.card) { const card = this.cgTierCard(R.card, `The Gilded Joker's daily challenge (${c.day}): the ${["bronze", "silver", "gold"][c.i]} mark.`, new CM.Random(CM.hashSeed(`${this.seed}:daily:${c.day}:${c.i}`))); if (card) out.cards.push(card); } } D.carry = []; this.gold += out.gold; const F = this.cgStore(); F.dailyGold = (F.dailyGold || 0) + out.gold; }
      else if (what === "streak") { if (!D.streakUnpaid) return out; D.streakUnpaid -= 1; D.streakPaid = (D.streakPaid || 0) + 1; const card = this.cgTierCard("rare", `A ${DAILY.streakCard}-day streak of the Gilded Joker's daily challenge.`, new CM.Random(CM.hashSeed(`${this.seed}:daily:streak:${D.streakPaid}`))); if (card) out.cards.push(card); }
      else { const i = Number(what); if (!D.got[i] || D.paid[i]) return out; D.paid[i] = true; const R = DAILY.REWARD[i]; out.gold = Math.round(R.gold * this.dlMult()); this.gold += out.gold; const F = this.cgStore(); F.dailyGold = (F.dailyGold || 0) + out.gold;
        if (R.card) { const card = this.cgTierCard(R.card, `The Gilded Joker's daily challenge (${D.day}): the ${["bronze", "silver", "gold"][i]} mark.`, new CM.Random(CM.hashSeed(`${this.seed}:daily:${D.day}:${i}`))); if (card) out.cards.push(card); } }
      this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out;
    },
    dlUnpaid() { const D = this.dlState(); return D.got.filter((g, i) => g && !D.paid[i]).length + (D.streakUnpaid || 0) + (D.carry || []).length; },
  });
}
