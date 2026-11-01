"use strict";
// The floor, easier to find your way round (v16.5): the party's favourite tables (starred), the tables it played
// lately, and which it has never tried (a "new" ribbon in the gallery); each table's own figures (times played, gold
// laid and paid back, the return so far, tickets won there, the best score on its board, when first and last
// played); the gallery sorted by most played, most tickets or by name. And a visit, counted from the door: how long,
// gold laid and paid back, the purse before and after, tickets won, the best moment (the biggest celebration, or
// failing that the biggest payout) and the cards won - shown when the party leaves. The window is 76zzo-lobby.js.
{ const LB = CM.LOBBY = { recent: 8 };
  const sum = (o) => Object.values(o || {}).reduce((a, b) => a + (b || 0), 0);
  const st0 = CM.Game.prototype.cgStake, pay0 = CM.Game.prototype.cgPay, cel0 = CM.Game.prototype.cgCelebrate;
  Object.assign(CM.Game.prototype, {
    lbStore() { const F = this.cgStore(); F.lobby = F.lobby || { fav: {}, recent: [], tried: {}, first: {}, last: {} }; return F.lobby; },
    // a table opened: tried, and to the front of the recent row
    lbTouch(id, now) { now = now === undefined ? Date.now() : now; const L = this.lbStore(); L.tried[id] = true; L.first[id] = L.first[id] || now; L.last[id] = now; L.recent = [id].concat(L.recent.filter((k) => k !== id)).slice(0, LB.recent); this.saveCasino && this.saveCasino(); },
    lbFav(id) { const L = this.lbStore(); if (L.fav[id]) delete L.fav[id]; else L.fav[id] = true; this.saveCasino && this.saveCasino(); return !!L.fav[id]; },
    lbIsFav(id) { return !!this.lbStore().fav[id]; },
    lbIsNew(id) { const F = this.cgStore(); return !this.lbStore().tried[id] && !F.played[id]; },
    lbBest(id) { const F = this.cgStore(), B = (F.boards || {})[id]; if (B && B.length) return { score: B[0].score, level: B[0].level }; const fa = F[`fa_${id}_best`]; return fa ? { score: fa } : null; },
    lbStats(id) { const F = this.cgStore(), L = this.lbStore(), T = this.tkStore ? this.tkStore() : { by: {} }, w = F.wagered[id] || 0, p = F.paid[id] || 0;
      return { played: F.played[id] || 0, wagered: w, paid: p, ret: w ? p / w : null, net: p - w, tickets: (T.by || {})[id] || 0, best: this.lbBest(id), first: L.first[id] || null, last: L.last[id] || null, fav: !!L.fav[id] }; },
    lbSort(list, how) { const F = this.cgStore(), T = this.tkStore ? this.tkStore() : { by: {} }, L = this.lbStore(), by = T.by || {};
      const key = how === "played" ? (id) => -((F.played[id] || 0) * 1000 + (L.last[id] ? 1 : 0)) : how === "tickets" ? (id) => -(by[id] || 0) : null;
      const out = list.slice(); if (how === "az") out.sort((a, b) => a[1].replace(/^The /, "").localeCompare(b[1].replace(/^The /, ""))); else if (key) out.sort((a, b) => key(a[0]) - key(b[0])); return out; },
    // ---- a visit to the Joker, counted from the door ----
    cgVisitStart(now) { const F = this.cgStore(), T = this.tkStore ? this.tkStore() : { earned: 0 }; this.cgVisit = { at: now === undefined ? Date.now() : now, gold: this.gold, tk: T.earned || 0, cards: F.cards.length, wag: sum(F.wagered), paid: sum(F.paid), best: null, top: null, tables: {} }; return this.cgVisit; },
    cgVisitEnd(now, peek) { const V = this.cgVisit; if (!V) return null; const F = this.cgStore(), T = this.tkStore ? this.tkStore() : { earned: 0 }; if (!peek) this.cgVisit = null;
      const out = { secs: Math.max(0, Math.round(((now === undefined ? Date.now() : now) - V.at) / 1000)), staked: sum(F.wagered) - V.wag, paid: sum(F.paid) - V.paid, before: V.gold, after: this.gold, tickets: (T.earned || 0) - V.tk, cards: F.cards.slice(V.cards), tables: Object.keys(V.tables) };
      out.best = V.best ? V.best.text : V.top ? `${V.top.n.toLocaleString("en")} gold at ${V.top.game}` : null; out.quiet = !out.staked && !out.paid && !out.tickets && !out.cards.length; return out; },
    cgStake(game, bet) { const why = st0.call(this, game, bet); if (!why && this.cgVisit) this.cgVisit.tables[game] = true; return why; },
    cgPay(game, amount) { const n = pay0.call(this, game, amount), V = this.cgVisit; if (V && n > 0) { V.tables[game] = true; if (!V.top || n > V.top.n) V.top = { n, game }; } return n; },
    cgCelebrate(tier, text) { cel0.call(this, tier, text); const V = this.cgVisit; if (V && (!V.best || tier > V.best.tier)) V.best = { tier, text }; },
  });
}
